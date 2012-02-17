# -*- coding: utf-8 -*-
import os
import logging

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.utils.translation import ugettext as _
from landez.reader import MBTilesReader, ExtractionError, InvalidFormatError
from landez.proj import GoogleProjection

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
                if ext != '.%s' % app_settings.MBTILES_EXT:
                    continue
                try:
                    mb = MBTiles(os.path.join(dirname, filename))
                    assert mb.name, _("%s name is empty !") % mb.id
                    yield mb
                except (AssertionError, InvalidFormatError), e:
                    logger.error(e)


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
        self._reader = MBTilesReader(self.fullpath, tilesize=app_settings.TILE_SIZE)

    @property
    def id(self):
        iD, ext = os.path.splitext(self.basename)
        return iD

    @property
    def name(self):
        return self.metadata.get('name', self.id)

    @property
    def filesize(self):
        return os.path.getsize(self.fullpath)

    @reify
    def metadata(self):
        return self._reader.metadata()

    @reify
    def bounds(self):
        bounds = self.metadata.get('bounds', '').split(',')
        if len(bounds) != 4:
            logger.warning(_("Invalid bounds metadata in '%s', fallback to whole world.") % self.name)
            bounds = [-180,-90,180,90]
        return tuple(map(float, bounds))

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

    @property
    def minzoom(self):
        z = self.metadata.get('minzoom', self.zoomlevels[0])
        return int(z)

    @property
    def maxzoom(self):
        z = self.metadata.get('maxzoom', self.zoomlevels[-1])
        return int(z)

    @property
    def middlezoom(self):
        return self.zoomlevels[len(self.zoomlevels)/2]

    @reify
    def zoomlevels(self):
        return self._reader.zoomlevels()

    def tile(self, z, x, y):
        try:
            return self._reader.tile(z, x, y)
        except ExtractionError:
            raise MissingTileError

    def center_tile(self):
        lon, lat, zoom = self.center
        proj = GoogleProjection(app_settings.TILE_SIZE, [zoom])
        return proj.tile_at(zoom, (lon, lat))

    def grid(self, z, x, y, callback=None):
        try:
            return self._reader.grid(z, x, y, callback)
        except ExtractionError:
            raise MissingTileError

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
