*django-mbtiles* serve maps from MBTiles files using Django. 
It mainly relies on `landez <https://github.com/makinacorpus/landez/>`_.

=======
INSTALL
=======

::

    pip install -r requirements.txt
    python setup.py install


=====
USAGE
=====

* Add ``mbtilesmap`` to your ``INSTALLED_APPS``
* Make sure you have ``'django.core.context_processors.static'`` in your `context processors <https://docs.djangoproject.com/en/dev/howto/static-files/#with-a-context-processor>`_

* Include mbtilesmap urls into your project

::

    urlpatterns = patterns('',
        ...
        ...
        url(r'^', include('mbtilesmap.urls', namespace='mb', app_name='mbtilesmap')),
    )

* Add the HTML header and call the template tag

::

    {% load mbtilesmap_tags %}
    ...
    {% block head %}
    {% include "mbtilesmap/head.html" %}
    {{ block.super }}
    {% endblock head %}
    
    ...
    ...
    {% mbtilesmap filename %}


Example
=======

You can find a working demo project (MBTiles maps browser *livembtiles*) 
in the ``example/`` folder of the source tree (see dedicated ``README.rst`` file).

=======
AUTHORS
=======

    * Mathieu Leplatre <mathieu.leplatre@makina-corpus.com>
    
|makinacom|_

.. |makinacom| image:: http://depot.makina-corpus.org/public/logo.gif
.. _makinacom:  http://www.makina-corpus.com


=======
LICENSE
=======

    * Lesser GNU Public License
