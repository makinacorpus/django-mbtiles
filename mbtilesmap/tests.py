import os

from django.test import TestCase

from mbtilesmap import app_settings
from mbtilesmap.models import (MBTiles, MBTilesManager, 
                               MBTilesFolderError, MBTilesNotFoundError)

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(FILE_PATH, 'fixtures')


class MBTilesTest(TestCase):
    def test_list(self):
        mgr = MBTilesManager()
        # Default settings folder
        self.failIfEqual(['france-6'], [o.name for o in mgr.all()])
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTilesManager)
        # Use fixtures folder
        app_settings.MBTILES_ROOT = FIXTURES_PATH
        mgr = MBTilesManager()
        self.failUnlessEqual(['france-6'], [o.name for o in mgr.all()])
        # Can be called twice with same result
        qs = mgr.all()
        self.failUnlessEqual(['france-6'], [o.name for o in qs])
        self.failUnlessEqual(['france-6'], [o.name for o in qs])
        # And is refreshed
        extrafile = os.path.join(FIXTURES_PATH, 'file.mbtiles')
        open(extrafile, 'w').close()
        self.failUnlessEqual(['france-6', 'file'], [o.name for o in mgr.all()])
        os.remove(extrafile)
        # File with different extensions are ignored
        extrafile = os.path.join(FIXTURES_PATH, 'file.wrong')
        open(extrafile, 'w').close()
        self.failUnlessEqual(['france-6'], [o.name for o in mgr.all()])
        # Except if we change the setting extension
        app_settings.MBTILES_EXT = 'wrong'
        self.failUnlessEqual(['file'], [o.name for o in mgr.all()])
        os.remove(extrafile)
        app_settings.MBTILES_EXT = 'mbtiles'

    def test_center(self):
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-6.mbtiles'))
        # Only one zoom level
        self.failUnlessEqual([6], mb.zoomlevels)
        c = mb.center()
        # MBTiles has no metadata, center will be (0, 0)
        self.failUnlessEqual((0, 0, 6), tuple(c))
        c = mb.center(3)
        self.failUnlessEqual((0, 0, 6), tuple(c))

    def test_name(self):
        # Existing file
        app_settings.MBTILES_ROOT = FIXTURES_PATH
        # full path
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-6.mbtiles'))
        self.failUnlessEqual('france-6', mb.name)
        # relative to MBTILES_ROOT
        mb = MBTiles('france-6.mbtiles')
        self.failUnlessEqual('france-6', mb.name)
        # with default extension
        mb = MBTiles('france-6')
        self.failUnlessEqual('france-6', mb.name)
        # Unknown file
        self.assertRaises(MBTilesNotFoundError, MBTiles, ('unknown.mbtiles'))
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTiles, ('unknown.mbtiles'))
