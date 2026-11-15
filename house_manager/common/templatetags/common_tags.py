"""Shared template tags."""
from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

register = template.Library()


@register.simple_tag
def breadcrumbs(house=None, client=None, current=""):
    """Render a breadcrumb trail from the Phase 1 URL hierarchy.

    Dashboard / House / Client / <current page> — every crumb is a link
    except the current page. Accepts the context objects available on
    hierarchy pages; anything omitted simply shortens the trail.
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
