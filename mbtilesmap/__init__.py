from django.conf import settings
from easydict import EasyDict


MBTILES_NAME_PATTERN = r'[\.\-\w]+'

app_settings = EasyDict(dict(
    MAP_URL_NAME = 'map',
    MBTILES_EXT = 'mbtiles',
    MBTILES_ROOT = settings.MEDIA_ROOT,
    TILE_SIZE = 256,
    CACHE_TIMEOUT = 60 * 60,  # 1 hour
), **getattr(settings, 'MBTILES_APP_CONFIG', {}))
