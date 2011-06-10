# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from views import tile


urlpatterns = patterns('',
    url(r'^(?P<name>[-\w]+)/(?P<z>\d+)/(?P<x>\d+)/(?P<y>\d+)/$', tile, name="tile"),
)
