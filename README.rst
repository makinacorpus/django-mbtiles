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


Example : a MBTiles map browser
-------------------------------
* Configure default MBTiles folder to load files by their name

::

    # settings.py
    PROJECT_ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
    
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

having this in ``index.html`` ::

    <ul>
    {% for map in maps %}
        <li><a href="{% url map map.name %}">{{ map.name }}</a></li>
    {% endfor %}
    </ul>


* A unique page for all maps (*complete previous* ``urls.py``):

::

    # urls.py 
    from django.views.generic import TemplateView
    from mbtilesmap import MBTILES_NAME_PATTERN

    class MyTemplateView(TemplateView):
        def get_context_data(self, **kwargs):
            return self.kwargs

    urlpatterns = patterns('',
        ...
        ...
        url(r'^(?P<name>%s)/$' % MBTILES_NAME_PATTERN, 
            MyTemplateView.as_view(template_name='map.html'),
            name="map"),

        url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
    )


with this in ``map.html`` 

::

    {% load mbtilesmap_tags %}

    {% block body %}
    {% mbtiles_map name %}
    {% endblock body %}
