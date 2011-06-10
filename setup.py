import os
from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-mbtiles',
    version='1.0',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    packages=[os.path.join(here, 'mbtilesmap')],
    url='https://github.com/makinacorpus/django-mbtiles',
    classifiers  = ['Topic :: Utilities', 
                    'Natural Language :: English',
                    'Operating System :: OS Independent',
                    'Intended Audience :: Developers',
                    'Environment :: Web Environment',
                    'Framework :: Django',
                    'Development Status :: 5 - Production/Stable',
                    'Programming Language :: Python :: 2.5'],
    description="Serve maps from MBTiles files",
    long_description=open(os.path.join(here, 'README')).read(),
    requires = open(os.path.join(here, 'requirements.txt')).readlines(),
)
