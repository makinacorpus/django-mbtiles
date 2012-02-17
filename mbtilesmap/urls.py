# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from . import MBTILES_ID_PATTERN
from views import tile, grid, jsonp, preview


urlpatterns = patterns('',
    url(r'^(?P<name>%s)/(?P<z>(\d+|\{z\}))/(?P<x>(\d+|\{x\}))/(?P<y>(\d+|\{y\})).png$' % MBTILES_ID_PATTERN, tile, name="tile"),
    url(r'^(?P<name>%s)/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+).grid.json$' % MBTILES_ID_PATTERN, grid, name="grid"),
    url(r'^(?P<name>%s)/preview.png$' % MBTILES_ID_PATTERN, preview, name="preview"),
    url(r'^(?P<name>%s).jsonp$' % MBTILES_ID_PATTERN, jsonp, name="jsonp"),
)
