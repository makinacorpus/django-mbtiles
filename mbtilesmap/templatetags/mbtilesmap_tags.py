from django import template

from mbtilesmap.models import MBTiles


register = template.Library()


@register.inclusion_tag('mbtilesmap/head.html')
def mbtilesmap_head():
    return {}


@register.inclusion_tag('mbtilesmap/map.html')
def mbtilesmap(name, catalog=None):
    mbtiles = MBTiles(name, catalog=catalog)
    return {'catalog': catalog,
            'map': mbtiles}
