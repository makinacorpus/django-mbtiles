from django.conf.urls.defaults import patterns, include, url
from django.views.generic import ListView, TemplateView

from mbtilesmap.models import MBTiles
from mbtilesmap import MBTILES_ID_PATTERN


class MyTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        return self.kwargs

urlpatterns = patterns('',
    url(r'^$', 
        ListView.as_view(queryset=MBTiles.objects.all(),
                         context_object_name='maps',
                         template_name='index.html'),
        name="index"),
    url(r'^(?P<name>%s)/$' % MBTILES_ID_PATTERN, 
        MyTemplateView.as_view(template_name='map.html'),
        name="map"),
    url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
)
