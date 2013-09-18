import json

from django.shortcuts import redirect
from django.http import HttpResponse
from django.views.generic import ListView, TemplateView
from django.core.urlresolvers import reverse
from django.http import Http404

from mbtilesmap.models import MBTiles, MBTilesNotFoundError


def index(request):
    catalog = MBTiles.objects.default_catalog()
    if catalog is None:
        return CatalogView.as_view()(request)
    return redirect('catalog', catalog=catalog)


class CatalogView(ListView):
    queryset = MBTiles.objects.all()
    context_object_name='maps'
    template_name='catalog.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CatalogView, self).get_context_data(*args, **kwargs)
        context['catalog'] = self.kwargs.get('catalog')
        return context

    def get_queryset(self):
        try:
            catalog = self.kwargs.get('catalog')
            qs = super(CatalogView, self).get_queryset()
            return qs.filter(catalog=catalog)
        except MBTilesNotFoundError:
            raise Http404


class JSONResponseMixin(object):
    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(
            self.convert_context_to_json(context),
            content_type='application/json',
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        catalog = self.kwargs.get('catalog')
        maps = []
        for _map in context['object_list']:
            tilejsonpath = reverse('mbtilesmap:tilejson', kwargs=dict(catalog=catalog, name=_map.id))
            tilejsonurl = self.request.build_absolute_uri(tilejsonpath)
            previewpath = reverse('mbtilesmap:preview', kwargs=dict(catalog=catalog, name=_map.id))
            previewurl = self.request.build_absolute_uri(previewpath)
            attrs = dict(id=_map.id,
                         name=_map.name,
                         preview=previewurl,
                         tilejson=tilejsonurl,
                         metadata=_map.metadata)
            maps.append(attrs)
        return json.dumps(dict(maps=maps))


class CatalogViewJSON(JSONResponseMixin, CatalogView):
    pass


catalog = CatalogView.as_view()
catalog_json = CatalogViewJSON.as_view()


class PreviewView(TemplateView):
    template_name='map.html'

preview = PreviewView.as_view()