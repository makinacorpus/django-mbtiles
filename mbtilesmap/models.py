import os
import sqlite3
import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _

from . import app_settings


logger = logging.getLogger(__name__)


class MissingTileError(Exception):
    pass

class MBTilesNotFound(Exception):
    pass


class MBTilesManager(models.Manager):
    def all(self):
        if not os.path.exists(app_settings.MBTILES_ROOT):
            raise ImproperlyConfigured(_("MBTILES_ROOT '%s' does not exist") % app_settings.MBTILES_ROOT)

        maps = []
        for dirname, dirnames, filenames in os.walk(app_settings.MBTILES_ROOT):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == '.%s'  % app_settings.MBTILES_EXT:
                    maps.append(name)
        return maps


class MBTiles(models.Model):
    
    objects = MBTilesManager()

    def __init__(self, name):
        filename = "%s.%s" % (name, app_settings.MBTILES_EXT)
        mbtiles_file = os.path.join(app_settings.MBTILES_ROOT, filename)
        if not os.path.exists(mbtiles_file):
            raise MBTilesNotFound(_("'%s' not found") % mbtiles_file)
        self.con = sqlite3.connect(mbtiles_file)
        self.cur = self.con.cursor()

    def center(self, zoom):
        #TODO: compute center based on available tiles
        return (0, 0)  # lon, lat, WGS84

    def zoomlevels(self):
        self.cur.execute('SELECT DISTINCT(zoom_level) FROM tiles ORDER BY zoom_level')
        return [row[0] for row in self.cur]

    def tile(self, z, x, y):
        self.cur.execute('''SELECT tile_data FROM tiles 
                            WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y))
        t = self.cur.fetchone()
        if not t:
            raise MissingTileError
        return t[0]
