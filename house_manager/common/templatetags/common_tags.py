"""Shared template tags."""
from urllib.parse import urlencode

from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def breadcrumbs(house=None, client=None, parent_label=None, parent_url=None,
                current=""):
    """Render a breadcrumb trail from the Phase 1 URL hierarchy.

    Dashboard / House / Client / <parent> / <current page> — every crumb
    is a link except the current page. Accepts the context objects
    available on hierarchy pages; anything omitted simply shortens the
    trail. `parent_label` + `parent_url` add one extra linked crumb
    (edit pages use it to link their list page, replacing the old back
    button).
    """
    crumbs = [(_("Dashboard"), reverse("dashboard"))]

    if house is not None:
        crumbs.append((
            f"{house.town}, {house.address}",
            reverse("details_house", kwargs={"house_pk": house.pk}),
        ))

    if client is not None:
        crumbs.append((
            client.family_name,
            reverse("details_client",
                    kwargs={"house_pk": client.house_id, "pk": client.pk}),
        ))

    if parent_label and parent_url:
        crumbs.append((str(parent_label), parent_url))

    if current:
        crumbs.append((str(current), None))

    items = []
    for label, url in crumbs:
        if url:
            items.append(format_html('<a href="{}">{}</a>', url, label))
        else:
            items.append(format_html('<span aria-current="page">{}</span>', label))

    separator = '<span class="breadcrumbs__sep" aria-hidden="true">/</span>'
    # str.join() loses the safe-marking of the pieces — re-mark the composed
    # trail (every piece is already HTML built by format_html above).
    rendered = mark_safe(separator.join(items))

    return format_html(
        '<nav class="breadcrumbs" aria-label="{}">{}</nav>',
        _("Breadcrumb"), rendered,
    )


@register.filter
def query_string(request):
    """The request's query string as ``?a=b`` — empty string when there is
    none. Bill rows and the payment form append it to their URLs so the
    list's filter (?is_paid / ?month) travels through the pay/undo chain
    and the out-of-band summary swap recomputes the same filtered view.
    """
    qs = request.GET.dict()
    encoded = urlencode(qs)
    return f"?{encoded}" if encoded else ""
