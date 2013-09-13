from django.conf.urls import patterns, include, url

from mbtilesmap import MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN
from .views import index, catalog, preview


urlpatterns = patterns('',
    url(r'^$', index, name="index"),
    url(r'^(?P<catalog>%s)/$' % MBTILES_CATALOG_PATTERN, catalog, name="catalog"),
    url(r'^(?P<name>%s)/map/$' % (MBTILES_ID_PATTERN), preview, name="map"),
    url(r'^(?P<catalog>%s)/(?P<name>%s)/map/$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), preview, name="map"),
    url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
)
