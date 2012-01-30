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
from utils import reify


logger = logging.getLogger(__name__)


class MissingTileError(Exception):
    pass

class MBTilesNotFoundError(Exception):
    pass

class MBTilesFolderError(ImproperlyConfigured):
    def __init__(self, *args, **kwargs):
        super(ImproperlyConfigured, self).__init__(_("MBTILES_ROOT '%s' does not exist") % app_settings.MBTILES_ROOT)


class MBTilesManager(object):
    """ List available MBTiles in MBTILES_ROOT """
    def __init__(self, *args, **kwargs):
        if not os.path.exists(app_settings.MBTILES_ROOT):
            raise MBTilesFolderError()
        self.folder = app_settings.MBTILES_ROOT

    def all(self):
        return self

    def __iter__(self):
        for dirname, dirnames, filenames in os.walk(self.folder):
            for filename in filenames:
                name, ext = os.path.splitext(filename)
                if ext == '.%s'  % app_settings.MBTILES_EXT:
                    yield MBTiles(os.path.join(dirname, filename))


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
        self._con = None
        self._cur = None

    def _query(self, sql, *args):
        """ Executes the specified `sql` query and returns the cursor """
        if not self._con:
            logger.debug(_("Open MBTiles file '%s'") % self.fullpath)
            self._con = sqlite3.connect(self.fullpath)
            self._cur = self._con.cursor()
        sql = ' '.join(sql.split())
        logger.debug(_("Execute query '%s' %s") % (sql, args))
        self._cur.execute(sql, *args)
        return self._cur

    @reify
    def name(self):
        name, ext = os.path.splitext(self.basename)
        return name

    @reify
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

    @reify
    def metadata(self):
        rows = self._query('SELECT name, value FROM metadata')
        rows = [(row[0], row[1]) for row in rows]
        metadata = dict(rows)
        bounds = metadata.get('bounds', '').split(',')
        if len(bounds) != 4:
            logger.warning(_("Invalid bounds metadata in '%s', fallback to whole world.") % self.name)
            bounds = [-180,-90,180,90]
        metadata['bounds'] = list(map(float, bounds))
        return metadata

    def center(self, zoom=None):
        """
        Return the center (x,y) of the map at this zoom level.
        """
        middlezoom = self.zoomlevels[len(self.zoomlevels)/2]
        if zoom is None:
            zoom = middlezoom
        if zoom not in self.zoomlevels:
            logger.warning(_("Invalid zoom level (%s), fallback to middle zoom (%s)") % (zoom, middlezoom))
            zoom = middlezoom
        bounds = self.metadata['bounds']
        lat = bounds[1] + (bounds[3] - bounds[1])/2
        lon = bounds[0] + (bounds[2] - bounds[0])/2
        return [lon, lat, zoom]

    @reify
    def minzoom(self):
        return self.zoomlevels[0]

    @reify
    def maxzoom(self):
        return self.zoomlevels[-1]

    @reify
    def zoomlevels(self):
        rows = self._query('SELECT DISTINCT(zoom_level) FROM tiles ORDER BY zoom_level')
        return [row[0] for row in rows]

    def tile(self, z, x, y):
        y_mercator = (2**int(z) - 1) - int(y)
        rows = self._query('''SELECT tile_data FROM tiles 
                              WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        t = rows.fetchone()
        if not t:
            raise MissingTileError
        return t[0]

    def grid(self, z, x, y, callback):
        y_mercator = (2**int(z) - 1) - int(y)
        rows = self._query('''SELECT grid FROM grids 
                              WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        t = rows.fetchone()
        if not t:
            raise MissingTileError
        grid_json = simplejson.loads(zlib.decompress(t[0]))
        
        rows = self._query('''SELECT key_name, key_json FROM grid_data
                              WHERE zoom_level=? AND tile_column=? AND tile_row=?;''', (z, x, y_mercator))
        # join up with the grid 'data' which is in pieces when stored in mbtiles file
        grid_json['data'] = {}
        grid_data = rows.fetchone()
        while grid_data:
            grid_json['data'][grid_data[0]] = simplejson.loads(grid_data[1])
            grid_data = rows.fetchone()
        return '%s(%s);' % (callback, simplejson.dumps(grid_json))
