from django.conf import settings
from easydict import EasyDict

app_settings = EasyDict(dict({
    'MBTILES_EXT' : 'mbtiles',
    'MBTILES_ROOT' : settings.MEDIA_ROOT,
    'TILE_SIZE' : 256,
}, **getattr(settings, 'MBTILES_APP_CONFIG', {})))
