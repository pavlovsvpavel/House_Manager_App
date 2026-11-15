import base64
import binascii
import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# A jSignature stroke SVG is a few KB; a 100 KB decoded cap is generous
# for real signatures while ruling out DB-bloat payloads.
MAX_SIGNATURE_DECODED_BYTES = 100 * 1024
MAX_SIGNATURE_BASE64_LENGTH = 140 * 1024  # base64 inflates by ~4/3

_SVG_PROLOG_RE = re.compile(rb"^<\?xml[^>?]*\?>")
_SVG_DOCTYPE_RE = re.compile(rb"^<!DOCTYPE[^>\[\]]*>", re.IGNORECASE)
_SVG_COMMENT_RE = re.compile(rb"^<!--.*?-->", re.DOTALL)
_SVG_TAG_RE = re.compile(rb"^<svg[\s>/]")


def _looks_like_svg(decoded):
    """Accept the shapes the signature pad emits: an optional XML prolog,
    an optional DOCTYPE (external only — an internal ``[...]`` subset
    would enable entity expansion, so it is rejected), a few XML comments
    (jSignature stamps one in), then the <svg> tag."""
    data = decoded.lstrip()
    for _ in range(8):  # bounded: one prolog/doctype + a handful of comments
        if data.startswith(b"<?xml"):
            match = _SVG_PROLOG_RE.match(data)
            if not match:
                return False
            data = data[match.end():].lstrip()
        elif data[:9].lower() == b"<!doctype":
            match = _SVG_DOCTYPE_RE.match(data)
            if not match:
                return False
            data = data[match.end():].lstrip()
        elif data.startswith(b"<!--"):
            match = _SVG_COMMENT_RE.match(data)
            if not match:
                return False
            data = data[match.end():].lstrip()
        else:
            break
    return bool(_SVG_TAG_RE.match(data))


def validate_char_field(value):
    allowed_symbols = " ()/-"

    if not all(char.isalpha() or char in allowed_symbols for char in value):
        raise ValidationError(_("Field should contain only letters, spaces, (), /, and -"))

    has_letter = any(char.isalpha() for char in value)
    if not has_letter:
        raise ValidationError(_("Field must contain at least one letter"))


def validate_phone_number(value):
    if not value.isdigit():
        raise ValidationError(_("Phone number should contains only digits"))

    elif len(value) != 10:
        raise ValidationError(_("Phone number should be exactly 10 digits"))


def validate_signature_payload(raw_base64):
    """Validate the raw base64 body the signature pad posts (#15).

    The value is stored as ``data:image/svg+xml;base64,...`` and rendered
    via ``<img src=...>``: cap the size and require the payload to decode
    to SVG markup, so tampered posts cannot bloat the DB or smuggle
    non-SVG content into a future rendering context. Returns the raw
    base64 unchanged; raises ValidationError otherwise.
    """
    if not raw_base64 or len(raw_base64) > MAX_SIGNATURE_BASE64_LENGTH:
        raise ValidationError(_("Invalid signature payload."))

    try:
        decoded = base64.b64decode(raw_base64, validate=True)
    except (binascii.Error, ValueError):
        raise ValidationError(_("Invalid signature payload."))

    if len(decoded) > MAX_SIGNATURE_DECODED_BYTES:
        raise ValidationError(_("Invalid signature payload."))

    if not _looks_like_svg(decoded):
        raise ValidationError(_("Invalid signature payload."))
