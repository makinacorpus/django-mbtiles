==============
Django-mbtiles
==============

Serve maps from MBTiles files


Installation
############

::

    pip install -r requirements.txt
    python setup.py install


Usage
#####

* Add ``mbtilesmap`` to your ``INSTALLED_APPS``

* Include mbtilesmap urls into your project

::

    urlpatterns = patterns('',
        ...
        ...
        url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
    )

* Add the map to your template

::

    {% load mbtilesmap_tags %}
    ...
    ...
    {% mbtiles_map filename %}


Advanced usage
--------------
* Configure default MBTiles folder to load files by their name

::

    # settings.py
    MBTILES_APP_CONFIG  =  {
        'MBTILES_ROOT' : os.path.join(PROJECT_ROOT_PATH, 'data')
    }

* An index page to list all available MBTiles files

::

    # urls.py
    from django.views.generic import ListView
    
    from mbtilesmap.models import MBTiles
    
    urlpatterns = patterns('',
        url(r'^$', 
            ListView.as_view(queryset=MBTiles.objects.all(),
                             context_object_name='maps',
                             template_name='index.html'),
            name='index')
        ...
        ...
    )
