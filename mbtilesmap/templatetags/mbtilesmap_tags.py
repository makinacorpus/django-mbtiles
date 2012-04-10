from django import template

from mbtilesmap.models import MBTiles


register = template.Library()


@register.simple_tag
def mbtilesmap_head():
    c = template.Context()
    return template.loader.get_template('mbtilesmap/head.html').render(c)


class MapNode(template.Node):
    def __init__(self, name):
        self.name = template.Variable(name)
        self.mbtiles = None

    def render(self, context):
        name = self.name.resolve(context)
        self.mbtiles = MBTiles(name)

        t = template.loader.get_template('mbtilesmap/map.html')

        c = template.Context({'map': self.mbtiles},
                             autoescape=context.autoescape)
        return t.render(c)


@register.tag(name="mbtilesmap")
def do_mbtilesmap(parser, token):
    """
    {% mbtiles_map name %}

    Renders a map for specified MBTiles file
    """
    args = token.split_contents()
    if len(args) < 2:
        raise template.TemplateSyntaxError('mbtiles_map takes at least one '
                                           'argument')
    return MapNode(args[1])
