from django.conf.urls import patterns, include, url

from mbtilesmap import MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN
from .views import index, catalog, catalog_json, preview


urlpatterns = patterns('',
    url(r'^$', index, name="index"),
    url(r'^(?P<catalog>%s)/$' % MBTILES_CATALOG_PATTERN, catalog, name="catalog"),
    url(r'^(?P<catalog>%s).json$' % MBTILES_CATALOG_PATTERN, catalog_json, name="catalog_json"),
    url(r'^(?P<name>%s)/map/$' % (MBTILES_ID_PATTERN), preview, name="map"),
    url(r'^(?P<catalog>%s)/(?P<name>%s)/map/$' % (MBTILES_CATALOG_PATTERN, MBTILES_ID_PATTERN), preview, name="map"),
    url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
)
