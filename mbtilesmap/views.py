import logging

from django.http import Http404, HttpResponse
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page

from . import app_settings
from models import MBTiles, MissingTileError, MBTilesNotFoundError


logger = logging.getLogger(__name__)


def tile(request, name, z, x, y):
    """ Serve a single tile """
    try:
        mbtiles = MBTiles(name)
        data = mbtiles.tile(z, x, y)
        response = HttpResponse(mimetype='image/png')
        response.write(data)
        return response
    except MBTilesNotFoundError, e:
        logger.warning(e)
    except MissingTileError:
        logger.warning(_("Tile %s not available in %s") % ((z, x, y), name))
    raise Http404


@cache_page(app_settings.CACHE_TIMEOUT_JSONP)
def jsonp(request, name):
    """ Serve the map configuration as JSONP """
    mbtiles = MBTiles(name)
    return HttpResponse(
        mbtiles.jsonp,
        content_type = 'application/javascript; charset=utf8'
    )
