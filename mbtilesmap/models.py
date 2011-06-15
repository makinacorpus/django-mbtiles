import os
import sqlite3
import logging

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext as _
from landez.proj import GoogleProjection

from . import app_settings


logger = logging.getLogger(__name__)


class MissingTileError(Exception):
    pass

class MBTilesNotFoundError(Exception):
    pass

class MBTilesFolderError(ImproperlyConfigured):
    def __init__(self, *args, **kwargs):
        super(ImproperlyConfigured, self).__init__(_("MBTILES_ROOT '%s' does not exist") % app_settings.MBTILES_ROOT)


def connectdb(*args):
    """ A decorator for a lazy database connection """
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            if not self.con:
                self.con = sqlite3.connect(self.fullpath)
                self.cur = self.con.cursor()
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


class MBTilesManager(models.Manager):
    """ List available MBTiles in MBTILES_ROOT """
    def get_query_set(self):
        # TODO: return QuerySet object!
        if not os.path.exists(app_settings.MBTILES_ROOT):
            raise MBTilesFolderError()

        maps = []
        for dirname, dirnames, filenames in os.walk(app_settings.MBTILES_ROOT):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == '.%s'  % app_settings.MBTILES_EXT:
                    maps.append(MBTiles(os.path.join(dirname, filename)))
        return maps


class MBTiles(models.Model):
    """ Represent a MBTiles file """

    objects = MBTilesManager()

    def __init__(self, name):
        """
        Load a MBTile file.
        If `name` is a valid filepath, it will load it. 
        Else, it will attempt to load it within `settings.MBTILES_ROOT` folder.
        """
        mbtiles_file = name
        if not os.path.exists(mbtiles_file):
            if not os.path.exists(app_settings.MBTILES_ROOT):
                raise MBTilesFolderError()
            mbtiles_file = os.path.join(app_settings.MBTILES_ROOT, name)
            if not os.path.exists(mbtiles_file):
                mbtiles_file = "%s.%s" % (mbtiles_file, app_settings.MBTILES_EXT)
                if not os.path.exists(mbtiles_file):
                    raise MBTilesNotFoundError(_("'%s' not found") % mbtiles_file)
        self.fullpath = mbtiles_file
        self.con = None
        self.cur = None

    @property
    def name(self):
        name, ext = os.path.splitext(os.path.basename(self.fullpath))
        return name

    @connectdb()
    def center(self, zoom):
        """
        Return the center (x,y) of the map at this zoom level.
        """
        # Find a group of adjacent available tiles at this zoom level
        self.cur.execute('''SELECT tile_column, tile_row FROM tiles 
                            WHERE zoom_level=? 
                            ORDER BY tile_column, tile_row;''', (zoom,))
        t = self.cur.fetchone()
        xmin, ymin = t
        previous = t
        while t and t[0] - previous[0] <= 1:
            # adjacent, go on
            previous = t
            t = self.cur.fetchone()
        xmax, ymax = previous
        # Transform (xmin, ymin) (xmax, ymax) to pixels
        S = app_settings.TILE_SIZE
        bottomleft = (xmin * S, (ymax + 1) * S)
        topright = ((xmax + 1) * S, ymin * S)
        # Determine center of rectangle
        width = topright[0] - bottomleft[0]
        height = bottomleft[1] - topright[1]
        center = (topright[0] - (width/2), 
                  bottomleft[1] - (height/2))
        # Convert center to (lon, lat)
        proj = GoogleProjection(S, [zoom])  # WGS84
        return proj.fromPixelToLL(center, zoom)

    @connectdb()
    def zoomlevels(self):
        self.cur.execute('SELECT DISTINCT(zoom_level) FROM tiles ORDER BY zoom_level')
        return [row[0] for row in self.cur]

    @connectdb()
    def tile(self, z, x, y):
        self.cur.execute('''SELECT tile_data FROM tiles 
                            WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y))
        t = self.cur.fetchone()
        if not t:
            raise MissingTileError
        return t[0]
