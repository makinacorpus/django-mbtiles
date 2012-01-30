import os

from django.test import TestCase

from mbtilesmap.models import MBTiles

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(FILE_PATH, 'fixtures')


class MBTilesTest(TestCase):
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
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-6.mbtiles'))
        self.failUnlessEqual('france-6', mb.name)
