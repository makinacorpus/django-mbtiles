*livembtiles* is a map browser, showing all MBTiles files in a folder.

=====
SETUP
=====

Install dependencies :

::

    make install

Run development server :

::

    make serve

==========
DEPLOYMENT
==========

::

    make install 

Then as root :

::

    aptitude install python-pkg-resources 
    ln -s etc/init.d/gunicorn /etc/init.d/gunicorn
    chmod u+x /etc/init.d/gunicorn
    update-rc.d gunicorn defaults
    /etc/init.d/gunicorn start
    
    aptitude install nginx
    /etc/init.d/nginx start
    ln -s etc/nginx/livembtiles.conf /etc/nginx/sites-enabled/livembtiles.conf
    rm /etc/nginx/sites-enabled/default 
    /etc/init.d/nginx reload


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
