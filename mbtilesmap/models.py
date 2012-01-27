# -*- coding: utf-8 -*-
import os
import sqlite3
import logging
import zlib

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.utils.translation import ugettext as _

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


class MBTilesManager(object):
    """ List available MBTiles in MBTILES_ROOT """
    
    def all(self):
        if not os.path.exists(app_settings.MBTILES_ROOT):
            raise MBTilesFolderError()
        maps = []
        for dirname, dirnames, filenames in os.walk(app_settings.MBTILES_ROOT):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == '.%s'  % app_settings.MBTILES_EXT:
                    maps.append(MBTiles(os.path.join(dirname, filename)))
        return maps


class MBTiles(object):
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
        self.basename = os.path.basename(self.fullpath)
        self.con = None
        self.cur = None

    @property
    def name(self):
        name, ext = os.path.splitext(self.basename)
        return name

    @property
    def filesize(self):
        return os.path.getsize(self.fullpath)

    def jsonp(self, callback):
        tilepattern = reverse("mbtilesmap:tile", kwargs=dict(name=self.name, x='{x}',y='{y}',z='{z}'))
        tilepattern = tilepattern.replace('%7B', '{').replace('%7D', '}')
        jsonp = {
            "id": self.name,
            "scheme": "xyz",
            "basename": self.basename,
            "filesize": self.filesize,
            "minzoom": self.minzoom,
            "maxzoom": self.maxzoom,
            "center": self.center(),
            "tiles": [tilepattern],
        }
        jsonp.update(self.metadata)
        return '%s(%s);' % (callback, simplejson.dumps(jsonp))

    @property
    @connectdb()
    def metadata(self):
        self.cur.execute('SELECT name, value FROM metadata')
        rows = [(row[0], row[1]) for row in self.cur]
        metadata = dict(rows)
        bounds = metadata.get('bounds', '').split(',')
        if len(bounds) != 4:
            logger.warning(_("Invalid bounds metadata in '%s'") % self.name)
            bounds = [-180,-90,180,90]
        metadata['bounds'] = list(map(float, bounds))
        return metadata

    @connectdb()
    def center(self, zoom=None):
        """
        Return the center (x,y) of the map at this zoom level.
        """
        middlezoom = self.zoomlevels[len(self.zoomlevels)/2]
        if zoom is None:
            zoom = middlezoom
        bounds = self.metadata['bounds']
        lat = bounds[1] + (bounds[3] - bounds[1])/2
        lon = bounds[0] + (bounds[2] - bounds[0])/2
        return [lon, lat, middlezoom]

    @property
    def minzoom(self):
        return self.zoomlevels[0]

    @property
    def maxzoom(self):
        return self.zoomlevels[-1]

    @property
    @connectdb()
    def zoomlevels(self):
        self.cur.execute('SELECT DISTINCT(zoom_level) FROM tiles ORDER BY zoom_level')
        return [row[0] for row in self.cur]

    @connectdb()
    def tile(self, z, x, y):
        y_mercator = (2**int(z) - 1) - int(y)
        self.cur.execute('''SELECT tile_data FROM tiles 
                            WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        t = self.cur.fetchone()
        if not t:
            raise MissingTileError
        return t[0]

    @connectdb()
    def grid(self, z, x, y, callback):
        y_mercator = (2**int(z) - 1) - int(y)
        self.cur.execute('''SELECT grid FROM grids 
                            WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        t = self.cur.fetchone()
        if not t:
            raise MissingTileError
        grid_json = simplejson.loads(zlib.decompress(t[0]))
        
        self.cur.execute('''SELECT key_name, key_json FROM grid_data
                            WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        # join up with the grid 'data' which is in pieces when stored in mbtiles file
        grid_json['data'] = {}
        grid_data = self.cur.fetchone()
        while grid_data:
            grid_json['data'][grid_data[0]] = simplejson.loads(grid_data[1])
            grid_data = self.cur.fetchone()
        return '%s(%s);' % (callback, simplejson.dumps(grid_json))
