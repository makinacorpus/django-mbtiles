import os

from django.conf import settings
from easydict import EasyDict


MBTILES_ID_PATTERN = r'[\.\-_0-9a-zA-Z]+'
MBTILES_CATALOG_PATTERN = MBTILES_ID_PATTERN


app_settings = EasyDict(dict(
    MBTILES_EXT = 'mbtiles',
    MBTILES_ROOT = os.getenv('MBTILES_ROOT', os.path.join(settings.MEDIA_ROOT, 'data')),
    TILE_SIZE = 256,
    MISSING_TILE_404 = False,
), **getattr(settings, 'MBTILES_APP_CONFIG', {}))
