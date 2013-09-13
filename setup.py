import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-mbtiles',
    version='1.2',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    url='https://github.com/makinacorpus/django-mbtiles',
    download_url = "http://pypi.python.org/pypi/django-mbtiles/",
    description="Serve maps from MBTiles files using Django",
    long_description=open(os.path.join(here, 'README.rst')).read(),
    install_requires = open(os.path.join(here, 'requirements.txt')).readlines(),
    packages=find_packages(),
    classifiers  = ['Topic :: Utilities', 
                    'Natural Language :: English',
                    'Operating System :: OS Independent',
                    'Intended Audience :: Developers',
                    'Environment :: Web Environment',
                    'Framework :: Django',
                    'Development Status :: 5 - Production/Stable',
                    'Programming Language :: Python :: 2.5'],
)
