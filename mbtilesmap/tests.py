import os
import re
import hashlib
import shutil

from django.utils import simplejson
from django.test import TestCase
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse, NoReverseMatch
from easydict import EasyDict as edict

from . import app_settings, MBTILES_ID_PATTERN
from models import (MBTiles, MBTilesManager, 
                    MBTilesFolderError, MBTilesNotFoundError)


FILE_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURES_PATH = os.path.join(FILE_PATH, 'fixtures')
app_settings.MBTILES_ROOT = FIXTURES_PATH
MBTiles.objects.folder = FIXTURES_PATH


class MBTilesManagerTest(TestCase):

    def setUp(self):
        self.root_orig = app_settings.MBTILES_ROOT
        self.mgr = MBTilesManager()

    def tearDown(self):
        app_settings.MBTILES_ROOT = self.root_orig

    def test_files_in_folder(self):
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in self.mgr.all()]))
        # Can be called twice with same result
        qs = self.mgr.all()
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in qs]))
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in qs]))

    def test_files_list_is_dynamic(self):
        extrafile = os.path.join(FIXTURES_PATH, 'file.mbtiles')
        shutil.copyfile(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'), extrafile)
        self.failUnlessEqual(['file', 'france-35', 'geography-class'], sorted([o.id for o in self.mgr.all()]))
        os.remove(extrafile)

    def test_unsupported_extensions_are_ignored(self):
        extrafile = os.path.join(FIXTURES_PATH, 'file.wrong')
        shutil.copyfile(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'), extrafile)
        self.failUnlessEqual(['france-35', 'geography-class'], sorted([o.id for o in self.mgr.all()]))
        # Except if we change the setting extension
        app_settings.MBTILES_EXT = 'wrong'
        self.failUnlessEqual(['file'], [o.id for o in self.mgr.all()])
        os.remove(extrafile)
        app_settings.MBTILES_EXT = 'mbtiles'

    def test_no_error_if_folder_is_empty(self):
        # Try a folder without mbtiles
        app_settings.MBTILES_ROOT = '.'
        self.mgr = MBTilesManager()
        self.failIfEqual(['france-35'], [o.id for o in self.mgr.all()])

    def test_error_if_folder_is_missing(self):
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesFolderError, MBTilesManager)


class MBTilesManagerCatalogsTest(MBTilesManagerTest):

    def setUp(self):
        super(MBTilesManagerCatalogsTest, self).setUp()
        try:
            os.mkdir('/tmp/pouet')
            shutil.copy(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'), '/tmp/pouet/country.mbtiles')
        except OSError:
            pass

    def tearDown(self):
        super(MBTilesManagerCatalogsTest, self).tearDown()
        try:
            shutil.rmtree('/tmp/pouet')
        except OSError:
            pass

    def test_transparent_if_catalog_is_default(self):
        fullpath = self.mgr.catalog_path('fixtures')
        self.assertEqual(fullpath, app_settings.MBTILES_ROOT)

    def test_error_if_catalog_is_unknown(self):
        self.assertRaises(MBTilesNotFoundError, self.mgr.catalog_path, ('pouet'))

    def test_default_catalog_is_first_in_list(self):
        app_settings.MBTILES_ROOT += ":/tmp/pouet"
        default = self.mgr.default_catalog()
        self.assertEqual(default, 'fixtures')

        app_settings.MBTILES_ROOT = "/tmp/pouet:" + app_settings.MBTILES_ROOT
        default = self.mgr.default_catalog()
        self.assertEqual(default, 'pouet')

    def test_manager_should_support_multiple_folders(self):
        app_settings.MBTILES_ROOT = "/tmp/pouet:" + app_settings.MBTILES_ROOT
        MBTilesManager()

    def test_manager_should_fail_if_folder_does_not_exist(self):
        app_settings.MBTILES_ROOT = "/tmp/paf:" + app_settings.MBTILES_ROOT
        self.assertRaises(MBTilesFolderError, MBTilesManager)

    def test_manager_should_fail_if_catalog_does_not_exist(self):
        self.assertRaises(MBTilesNotFoundError, self.mgr.filter, catalog='paf')

    def test_manager_should_restrict_list_to_catalog(self):
        app_settings.MBTILES_ROOT += ":/tmp/pouet"

        self.mgr = MBTilesManager()
        listed = sorted([o.id for o in self.mgr.all()])
        self.failUnlessEqual(['france-35', 'geography-class'], listed)

        listed = sorted([o.id for o in self.mgr.filter(catalog='pouet').all()])
        self.failUnlessEqual(['country'], listed)

    def test_mbtiles_should_fail_if_mbtiles_does_not_exist(self):
        app_settings.MBTILES_ROOT += ":/tmp/pouet"
        MBTiles('country', catalog='pouet')
        self.assertRaises(MBTilesNotFoundError, MBTiles, 'country', catalog='paf')


class MBTilesModelTest(TestCase):

    def setUp(self):
        self.root_orig = app_settings.MBTILES_ROOT

    def tearDown(self):
        app_settings.MBTILES_ROOT = self.root_orig

    def test_bounds_are_world_if_no_metadata(self):
        mb = MBTiles('france-35')
        # MBTiles has no metadata, bounds will be (-180, -90, 180, 90)
        self.failUnlessEqual((-180, -90, 180, 90), mb.bounds)

    def test_bounds_come_from_metadata(self):
        mb = MBTiles('geography-class')
        self.failUnlessEqual((-18.6328, 32.25, 29.8828, 60.2398), mb.bounds)

    def test_center_is_0_0_if_no_metadata(self):
        mb = MBTiles('france-35')
        # Only one zoom level
        self.failUnlessEqual([3, 5], mb.zoomlevels)
        c = mb.center
        # MBTiles has no metadata, center will be (0, 0)
        self.failUnlessEqual((0, 0, 5), tuple(c))

    def test_center_come_from_metadata(self):
        mb = MBTiles('geography-class')
        # Center is in metadata 
        self.failUnlessEqual('2.3401,48.8503,7', mb.metadata.get('center'))
        # But zoomlevel is not among available
        self.failUnless(7 not in mb.zoomlevels)
        # Middle zoom is used
        self.failUnlessEqual(3, mb.middlezoom)
        self.failUnlessEqual((2.3401, 48.8503, 3), mb.center)

    def test_id_is_filename(self):
        # full path
        mb = MBTiles(os.path.join(FIXTURES_PATH, 'france-35.mbtiles'))
        self.failUnlessEqual('france-35', mb.id)
        # relative to MBTILES_ROOT
        mb = MBTiles('france-35.mbtiles')
        self.failUnlessEqual('france-35', mb.id)
        # with default extension
        mb = MBTiles('france-35')
        self.failUnlessEqual('france-35', mb.id)

    def test_raise_mbtiles_not_found(self):
        # Unknown file
        self.assertRaises(MBTilesNotFoundError, MBTiles, ('unknown.mbtiles'))

    def test_raise_folder_not_found(self):
        app_settings.MBTILES_ROOT = "random-path-xyz"
        self.assertRaises(MBTilesNotFoundError, MBTiles, ('unknown.mbtiles'))

    def test_filesize(self):
        mb = MBTiles('france-35')
        self.failUnlessEqual(117760, mb.filesize)

    def test_name_come_from_metadata(self):
        # Name in metadata
        mb = MBTiles('geography-class')
        self.failUnlessEqual('geography-class', mb.id)
        self.failUnlessEqual(u'Geography Class', mb.name)

    def test_name_is_filename_if_no_metadata(self):
        # No name in metadata
        mb = MBTiles('france-35')
        self.failUnlessEqual(mb.name, mb.id)


class MBTilesContentTest(TestCase):

    def test_jsonp(self):
        request = RequestFactory().get('/')
        mb = MBTiles('geography-class')
        js = mb.jsonp(request, 'cb')
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
        tile = mb.grid(3, 4, 2, callback='grid')
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


class MBTilesContentViewsTest(TestCase):

    def test_should_serve_image_if_exists(self):
        # Tiles
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='geography-class',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'image/png')

    def test_should_serve_404_if_mbtiles_missing(self):
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='class-geography',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 404)

    def test_should_serve_empty_if_tile_missing(self):
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='geography-class',
                                                                          x='3', y='18', z='22')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, '')

    def test_should_serve_404_if_tile_missing_setting(self):
        app_settings.MISSING_TILE_404 = True
        response = self.client.get(reverse('mbtilesmap:tile', kwargs=dict(name='geography-class',
                                                                          x='3', y='18', z='22')))
        self.assertEqual(response.status_code, 404)
        app_settings.MISSING_TILE_404 = False

    def test_should_serve_grid_if_exists(self):
        response = self.client.get(reverse('mbtilesmap:grid', kwargs=dict(name='geography-class',
                                                                          z='2', x='2', y='1')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/javascript; charset=utf8')

    def test_should_serve_404_if_grid_missing(self):
        response = self.client.get(reverse('mbtilesmap:grid', kwargs=dict(name='geography-class',
                                                                          x='3', y='18', z='22')))
        self.assertEqual(response.status_code, 404)

    def test_should_serve_tilejson_if_exists(self):
        response = self.client.get(reverse('mbtilesmap:tilejson', kwargs=dict(name='geography-class')))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-type'], 'application/javascript; charset=utf8')

    def test_should_serve__404_if_mbtiles_tilejson_missing(self):
        response = self.client.get(reverse('mbtilesmap:tilejson', kwargs=dict(name='class-geography')))
        self.assertEqual(response.status_code, 404)

    def test_url_patterns(self):
        self.failUnlessEqual('/geography-class/2/2/1.png', reverse('mbtilesmap:tile', kwargs=dict(name='geography-class', z='2', x='2', y='1')))
        self.failUnlessEqual('/geography-class/%7Bz%7D/%7Bx%7D/%7By%7D.png', reverse('mbtilesmap:tile', kwargs=dict(name='geography-class', z='{z}', x='{x}', y='{y}')))
        self.assertRaises(NoReverseMatch, reverse, ('mbtilesmap:tile'), kwargs=dict(name='geography-class', z='{z}', x='{y}', y='{x}'))
        self.assertRaises(NoReverseMatch, reverse, ('mbtilesmap:tile'), kwargs=dict(name='geography-class', z='z', x='y', y='x'))

    def test_url_patterns_with_catalog(self):
        self.failUnlessEqual('/fixtures/geography-class/2/2/1.png', reverse('mbtilesmap:tile', kwargs=dict(catalog='fixtures', name='geography-class', z='2', x='2', y='1')))
        self.failUnlessEqual('/fixtures/geography-class/%7Bz%7D/%7Bx%7D/%7By%7D.png', reverse('mbtilesmap:tile', kwargs=dict(catalog='fixtures', name='geography-class', z='{z}', x='{x}', y='{y}')))

    def test_patterns_filenames_match(self):
        p = re.compile('^%s$' % MBTILES_ID_PATTERN)
        self.failUnless(p.match('file.subname'))
        self.failUnless(p.match('file.subname.mbtiles'))
        self.failUnless(p.match('file-test'))
        self.failUnless(p.match('file_1234'))

        self.failIf(p.match('file+1234'))
        self.failIf(p.match('file/1234'))
        self.failIf(p.match('file"'))
