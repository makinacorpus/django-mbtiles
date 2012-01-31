import os

from django.test import TestCase

from mbtilesmap import app_settings
from mbtilesmap.models import (MBTiles, MBTilesManager, 
                               MBTilesFolderError, MBTilesNotFoundError)

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(FILE_PATH, 'fixtures')


class MBTilesTest(TestCase):
    def setUp(self):
        app_settings.MBTILES_ROOT = FIXTURES_PATH

    def test_list(self):
        # Use fixtures folder
        mgr = MBTilesManager()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.name for o in mgr.all()]))
        # Can be called twice with same result
        qs = mgr.all()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.name for o in qs]))
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.name for o in qs]))
        # And is refreshed
        extrafile = os.path.join(FIXTURES_PATH, 'file.mbtiles')
        open(extrafile, 'w').close()
        self.failUnlessEqual(['file', 'france-35', 'geography-class'], sorted([o.name for o in mgr.all()]))
        os.remove(extrafile)
        # File with different extensions are ignored
        extrafile = os.path.join(FIXTURES_PATH, 'file.wrong')
        open(extrafile, 'w').close()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.name for o in mgr.all()]))
        # Except if we change the setting extension
        app_settings.MBTILES_EXT = 'wrong'
        self.failUnlessEqual(['file'], [o.name for o in mgr.all()])
        os.remove(extrafile)
        app_settings.MBTILES_EXT = 'mbtiles'
        # Try a folder without mbtiles
        app_settings.MBTILES_ROOT = '.'
        mgr = MBTilesManager()
        self.failIfEqual(['france-35'], [o.name for o in mgr.all()])
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTilesManager)

    def test_bounds(self):
        mb = MBTiles('france-35')
        # MBTiles has no metadata, bounds will be (-180, -90, 180, 90)
        self.failUnlessEqual((-180, -90, 180, 90), mb.bounds)
        mb = MBTiles('geography-class')
        self.failUnlessEqual((-18.6328, 32.25, 29.8828, 60.2398), mb.bounds)

    def test_center(self):
        mb = MBTiles('france-35')
        # Only one zoom level
        self.failUnlessEqual([3,5], mb.zoomlevels)
        c = mb.center
        # MBTiles has no metadata, center will be (0, 0)
        self.failUnlessEqual((0, 0, 5), tuple(c))
        mb = MBTiles('geography-class')
        # Center is in metadata 
        self.failUnlessEqual('2.3401,48.8503,7', mb.metadata.get('center'))
        # But zoomlevel is not among available
        self.failUnless(7 not in mb.zoomlevels)
        # Middle zoom is used
        self.failUnlessEqual(3, mb.middlezoom)
        self.failUnlessEqual((2.3401, 48.8503, 3), mb.center)

    def test_name(self):
        # full path
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'))
        self.failUnlessEqual('france-35', mb.name)
        # relative to MBTILES_ROOT
        mb = MBTiles('france-35.mbtiles')
        self.failUnlessEqual('france-35', mb.name)
        # with default extension
        mb = MBTiles('france-35')
        self.failUnlessEqual('france-35', mb.name)
        # Unknown file
        self.assertRaises(MBTilesNotFoundError, MBTiles, ('unknown.mbtiles'))
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTiles, ('unknown.mbtiles'))

    def test_filesize(self):
        mb = MBTiles('france-35')
        self.failUnlessEqual(117760, mb.filesize)
