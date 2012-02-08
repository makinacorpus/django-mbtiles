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
    def id(self):
        iD, ext = os.path.splitext(self.basename)
        return iD

    @reify
    def name(self):
        return self.metadata.get('name', self.id)

    @reify
    def filesize(self):
        return os.path.getsize(self.fullpath)

    def jsonp(self, callback):
        # Raw metadata
        jsonp = dict(self.metadata)
        # Post-processed metadata
        jsonp.update(**{
            "bounds": self.bounds,
            "center": self.center,
            "minzoom": self.minzoom,
            "maxzoom": self.maxzoom,
        })
        # Additionnal info
        tilepattern = reverse("mbtilesmap:tile", kwargs=dict(name=self.id, x='{x}',y='{y}',z='{z}'))
        tilepattern = tilepattern.replace('%7B', '{').replace('%7D', '}')
        jsonp.update(**{
            "id": self.id,
            "name": self.name,
            "scheme": "xyz",
            "basename": self.basename,
            "filesize": self.filesize,
            "tiles": [tilepattern],
        })
        return '%s(%s);' % (callback, simplejson.dumps(jsonp))

    @reify
    def metadata(self):
        rows = self._query('SELECT name, value FROM metadata')
        rows = [(row[0], row[1]) for row in rows]
        return dict(rows)

    @reify
    def center(self):
        """
        Return the center (x,y) of the map at this zoom level.
        """
        center = self.metadata.get('center', '').split(',')
        if len(center) == 3:
            lon, lat, zoom = map(float, center)
            zoom = int(zoom)
            if zoom not in self.zoomlevels:
                logger.warning(_("Invalid zoom level (%s), fallback to middle zoom (%s)") % (zoom, self.middlezoom))
                zoom = self.middlezoom
            return (lon, lat, zoom)
        # Invalid center from metadata, guess center from bounds
        lat = self.bounds[1] + (self.bounds[3] - self.bounds[1])/2
        lon = self.bounds[0] + (self.bounds[2] - self.bounds[0])/2
        return (lon, lat, self.middlezoom)

    @reify
    def bounds(self):
        bounds = self.metadata.get('bounds', '').split(',')
        if len(bounds) != 4:
            logger.warning(_("Invalid bounds metadata in '%s', fallback to whole world.") % self.name)
            bounds = [-180,-90,180,90]
        return tuple(map(float, bounds))

    @reify
    def minzoom(self):
        z = self.metadata.get('minzoom', self.zoomlevels[0])
        return int(z)

    @reify
    def maxzoom(self):
        z = self.metadata.get('maxzoom', self.zoomlevels[-1])
        return int(z)

    @reify
    def middlezoom(self):
        return self.zoomlevels[len(self.zoomlevels)/2]

    @reify
    def zoomlevels(self):
        rows = self._query('SELECT DISTINCT(zoom_level) FROM tiles ORDER BY zoom_level')
        return [int(row[0]) for row in rows]

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
