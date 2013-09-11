# -*- coding: utf-8 -*-
import os
import logging
import json

from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from landez.sources import MBTilesReader, ExtractionError, InvalidFormatError
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
        for path in self._paths:
            if not os.path.exists(path):
                raise MBTilesFolderError()
        self.folder = self._paths[0]

    def filter(self, catalog=None):
        if catalog:
            self.folder = self.catalog_path(catalog)
        return self

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

    @property
    def _paths(self):
        return app_settings.MBTILES_ROOT.split(':')

    def default_catalog(self):
        path = self._paths[0]
        return os.path.basename(path)

    def catalog_path(self, catalog):
        try:
            return [p for p in self._paths if p.endswith(catalog)][0]
        except IndexError:
            raise MBTilesNotFoundError(_("Catalog '%s' not found.") % catalog)

    def fullpath(self, name, catalog=None):
        if os.path.exists(name):
            return name

        if catalog is None:
            basepath = self.folder
        else:
            basepath = self.catalog_path(catalog)

        mbtiles_file = os.path.join(basepath, name)
        if os.path.exists(mbtiles_file):
            return mbtiles_file

        mbtiles_file = "%s.%s" % (mbtiles_file, app_settings.MBTILES_EXT)
        if os.path.exists(mbtiles_file):
            return mbtiles_file

        raise MBTilesNotFoundError(_("'%s' not found in %s") % (mbtiles_file, self._paths))


class MBTiles(object):
    """ Represent a MBTiles file """

    objects = MBTilesManager()

    def __init__(self, name, catalog=None):
        self.fullpath = self.objects.fullpath(name, catalog)
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

    def jsonp(self, request, callback):
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
        tilepattern = request.build_absolute_uri(tilepattern)
        tilepattern = tilepattern.replace('%7B', '{').replace('%7D', '}')
        jsonp.update(**{
            "id": self.id,
            "name": self.name,
            "scheme": "xyz",
            "basename": self.basename,
            "filesize": self.filesize,
            "tiles": [tilepattern],
        })
        return '%s(%s);' % (callback, json.dumps(jsonp))
