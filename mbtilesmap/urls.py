# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from . import MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN
from views import tile, grid, tilejson, preview


urlpatterns = patterns('',
    url(r'^(?P<name>%s)/(?P<z>(\d+|\{z\}))/(?P<x>(\d+|\{x\}))/(?P<y>(\d+|\{y\})).png$' % MBTILES_ID_PATTERN, tile, name="tile"),
    url(r'^(?P<name>%s)/(?P<z>(\d+|\{z\}))/(?P<x>(\d+|\{x\}))/(?P<y>(\d+|\{y\})).grid.json$' % MBTILES_ID_PATTERN, grid, name="grid"),
    url(r'^(?P<name>%s)/preview.png$' % MBTILES_ID_PATTERN, preview, name="preview"),
    url(r'^(?P<name>%s).json$' % MBTILES_ID_PATTERN, tilejson, name="tilejson"),

    url(r'^(?P<catalog>%s)/(?P<name>%s)/(?P<z>(\d+|\{z\}))/(?P<x>(\d+|\{x\}))/(?P<y>(\d+|\{y\})).png$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), tile, name="tile"),
    url(r'^(?P<catalog>%s)/(?P<name>%s)/(?P<z>(\d+|\{z\}))/(?P<x>(\d+|\{x\}))/(?P<y>(\d+|\{y\})).grid.json$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), grid, name="grid"),
    url(r'^(?P<catalog>%s)/(?P<name>%s)/preview.png$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), preview, name="preview"),
    url(r'^(?P<catalog>%s)/(?P<name>%s).json$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), tilejson, name="tilejson"),
)
