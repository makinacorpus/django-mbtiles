from django.conf import settings
from easydict import EasyDict


MBTILES_ID_PATTERN = r'[\.\-_0-9a-zA-Z]+'

app_settings = EasyDict(dict(
    MBTILES_EXT = 'mbtiles',
    MBTILES_ROOT = settings.MEDIA_ROOT,
    TILE_SIZE = 256,
    CACHE_TIMEOUT = 60 * 60,  # 1 hour
), **getattr(settings, 'MBTILES_APP_CONFIG', {}))
