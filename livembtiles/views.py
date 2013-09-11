from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.http import Http404

from mbtilesmap.models import MBTiles, MBTilesNotFoundError


def index(request):
    catalog = MBTiles.objects.default_catalog()
    return redirect('catalog', catalog=catalog)


class CatalogView(ListView):
    queryset = MBTiles.objects.all()
    context_object_name='maps'
    template_name='catalog.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CatalogView, self).get_context_data(*args, **kwargs)
        context['catalog'] = self.kwargs['catalog']
        return context

    def get_queryset(self):
        try:
            catalog = self.kwargs['catalog']
            qs = super(CatalogView, self).get_queryset()
            return qs.filter(catalog=catalog)
        except MBTilesNotFoundError:
            raise Http404

catalog = CatalogView.as_view()


class PreviewView(TemplateView):
    template_name='map.html'

preview = PreviewView.as_view()