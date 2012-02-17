import os
import re
import hashlib
import shutil

from django.utils import simplejson
from django.test import TestCase
from django.core.urlresolvers import reverse, NoReverseMatch
from easydict import EasyDict as edict

from . import app_settings, MBTILES_ID_PATTERN
from models import (MBTiles, MBTilesManager, 
                    MBTilesFolderError, MBTilesNotFoundError)


FILE_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(FILE_PATH, 'fixtures')


class MBTilesTest(TestCase):
    def setUp(self):
        app_settings.MBTILES_ROOT = FIXTURES_PATH

    def test_list(self):
        # Use fixtures folder
        mgr = MBTilesManager()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in mgr.all()]))
        # Can be called twice with same result
        qs = mgr.all()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in qs]))
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in qs]))
        # And is refreshed
        extrafile = os.path.join(FIXTURES_PATH, 'file.mbtiles')
        shutil.copyfile(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'), extrafile)
        self.failUnlessEqual(['file', 'france-35', 'geography-class'], sorted([o.id for o in mgr.all()]))
        os.remove(extrafile)
        # File with different extensions are ignored
        extrafile = os.path.join(FIXTURES_PATH, 'file.wrong')
        shutil.copyfile(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'), extrafile)
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in mgr.all()]))
        # Except if we change the setting extension
        app_settings.MBTILES_EXT = 'wrong'
        self.failUnlessEqual(['file'], [o.id for o in mgr.all()])
        os.remove(extrafile)
        app_settings.MBTILES_EXT = 'mbtiles'
        # Try a folder without mbtiles
        app_settings.MBTILES_ROOT = '.'
        mgr = MBTilesManager()
        self.failIfEqual(['france-35'], [o.id for o in mgr.all()])
        # Try with a bad (=empty) mbtiles file
        extrafile = os.path.join(FIXTURES_PATH, 'file.png')
        self.failIfEqual(['file'], [o.id for o in mgr.all()])
        open(extrafile, 'w').close()
        os.remove(extrafile)
        # Try a unexisting folder
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

    def test_id(self):
        # full path
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'))
        self.failUnlessEqual('france-35', mb.id)
        # relative to MBTILES_ROOT
        mb = MBTiles('france-35.mbtiles')
        self.failUnlessEqual('france-35', mb.id)
        # with default extension
        mb = MBTiles('france-35')
        self.failUnlessEqual('france-35', mb.id)
        # Unknown file
        self.assertRaises(MBTilesNotFoundError, MBTiles, ('unknown.mbtiles'))
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTiles, ('unknown.mbtiles'))

    def test_name(self):
        # Name in metadata
        mb = MBTiles('geography-class')
        self.failUnlessEqual('geography-class', mb.id)
        self.failUnlessEqual(u'Geography Class', mb.name)
        # No name in metadata
        mb = MBTiles('france-35')
        self.failUnlessEqual(mb.name, mb.id)

    def test_filesize(self):
        mb = MBTiles('france-35')
        self.failUnlessEqual(117760, mb.filesize)

    def test_jsonp(self):
        mb = MBTiles('geography-class')
        js = mb.jsonp('cb')
        p = re.compile("cb\((.+)\);")
        self.failUnless(p.match(js))
        jsonp = p.match(js).group(1)
        jsonp = edict(simplejson.loads(jsonp))
        self.failUnlessEqual('geography-class', mb.id)
        self.failUnlessEqual(mb.id, jsonp.id)
        self.failUnlessEqual(mb.name, jsonp.name)
        self.failUnlessEqual(mb.center, tuple(jsonp.center))
        self.failUnlessEqual([2.3401, 48.8503, 3], jsonp.center)

    def test_tile(self):
        mb = MBTiles('geography-class')
        tile = mb.tile(3, 4, 2)
        h = hashlib.md5(tile).hexdigest()
        self.failUnlessEqual('e7de86eeea4e558851a7c0f6cc3082ff', h)

    def test_preview(self):
        mb = MBTiles('geography-class')
        self.failUnlessEqual((2.3401, 48.8503, 3), mb.center)
        center = mb.center_tile()
        self.failUnlessEqual((3, 4, 2), center)
        h = hashlib.md5(mb.tile(*center)).hexdigest()
        self.failUnlessEqual('e7de86eeea4e558851a7c0f6cc3082ff', h)
        # HTTP
        response = self.client.get(reverse('mbtilesmap:preview', kwargs={'name':'geography-class'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'image/png')
        response = self.client.get(reverse('mbtilesmap:preview', kwargs={'name':'unknown'}))
        self.assertEqual(response.status_code, 404)

    def test_grid(self):
        mb = MBTiles('geography-class')
        tile = mb.grid(3, 4, 2)
        h = hashlib.md5(tile).hexdigest()
        self.failUnlessEqual('8d9cf7d9d0bef7cc1f0a37b49bf4cec7', h)
        p = re.compile("grid\((.+)\);")
        self.failUnless(p.match(tile))
        utfgrid = p.match(tile).group(1)
        utfgrid = edict(simplejson.loads(utfgrid))
        self.failUnlessEqual(utfgrid.grid[20:30], 
            [u'       !!!!!!!!!!!######### &  $$$$$     %%%%%%%%%%%%%%%%%%%%%%%', 
             u'        !!!!!!!!!###########     $       %%%%%%%%%%%%%%%%%%%%%%%', 
             u"        !!!!!!!!!######## #        '''' %%%%%%%%%%%%%%%%%%%%%%%%", 
             u"         !!!!!! ###########     ' ''''''%%%%%%%%%%%%%%%%%%%%%%%%", 
             u"        !!!!!!  #########       ' '''''%%%%%%%%%%%%%%%%%%%%%%%%%", 
             u"         !!!!   ########       ''''''''%%%%%%%%%%%%%%%%%%%%%%%%%", 
             u"          !!     #######           (('''%%%%%%%%%%%%%%%%%%%%%%%%", 
             u"               ) #######  #     (  ((('%%%%%%%%%%%%%%%%%%%%%%%%%",
             u'              )  ######## #    ((  (((((%%%%%%%%%%%%%%%%%%%%%%%%', 
             u'            )))   ######      ((((((((((%%%%%%%%%%%%%%%%%%%%%%%%'])
        c = ord('#') + 32
        if c >= 92: c = c + 1 
        if c >= 34: c = c + 1
        self.failUnlessEqual(utfgrid.data[str(c)]['ADMIN'], 'Estonia')
        self.failUnlessEqual(utfgrid.data[str(c)]['POP_EST'], 1299371)

    def test_status(self):
        # Tiles
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='geography-class',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'image/png')
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='class-geography',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 404)
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='geography-class',
                                                                          x='3', y='18', z='22')))
        self.assertEqual(response.status_code, 404)
        # UTF-grid
        response = self.client.get(reverse('mbtilesmap:grid', kwargs=dict(name='geography-class',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/javascript; charset=utf8')
        response = self.client.get(reverse('mbtilesmap:grid', kwargs=dict(name='geography-class',
                                                                          x='3', y='18', z='22')))
        self.assertEqual(response.status_code, 404)
        # JSON-P
        response = self.client.get(reverse('mbtilesmap:jsonp', kwargs=dict(name='geography-class')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/javascript; charset=utf8')
        response = self.client.get(reverse('mbtilesmap:jsonp', kwargs=dict(name='class-geography')))
        self.assertEqual(response.status_code, 404)

    def test_patterns(self):
        self.failUnlessEqual('/geography-class/2/2/1.png', reverse('mbtilesmap:tile', kwargs=dict(name='geography-class', z='2', x='2', y='1')))
        self.failUnlessEqual('/geography-class/%7Bz%7D/%7Bx%7D/%7By%7D.png', reverse('mbtilesmap:tile', kwargs=dict(name='geography-class', z='{z}', x='{x}', y='{y}')))
        self.assertRaises(NoReverseMatch, reverse, ('mbtilesmap:tile'), kwargs=dict(name='geography-class', z='{z}', x='{y}', y='{x}'))
        self.assertRaises(NoReverseMatch, reverse, ('mbtilesmap:tile'), kwargs=dict(name='geography-class', z='z', x='y', y='x'))

        p = re.compile('^%s$' % MBTILES_ID_PATTERN)
        self.failUnless(p.match('file.subname'))
        self.failUnless(p.match('file.subname.mbtiles'))
        self.failUnless(p.match('file-test'))
        self.failUnless(p.match('file_1234'))

        self.failIf(p.match('file+1234'))
        self.failIf(p.match('file/1234'))
        self.failIf(p.match('file"'))
