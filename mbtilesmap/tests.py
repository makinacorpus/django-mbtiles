import os

from django.test import TestCase

from mbtilesmap.models import MBTiles


def fixturespath(filename):
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, 'fixtures', filename)


class MBTilesTest(TestCase):
    def test_center(self):
        mb = MBTiles(fixturespath('france-6.mbtiles'))
        self.failUnlessEqual([6], mb.zoomlevels())
        c = mb.center(6)
        # Round lon/lat to 4 digits
        c = map(lambda x: round(x, 4), c)
        self.failUnlessEqual((2.8125, 47.0402), tuple(c))

    def test_name(self):
        mb = MBTiles(fixturespath('france-6.mbtiles'))
        self.failUnlessEqual('france-6', mb.name)
