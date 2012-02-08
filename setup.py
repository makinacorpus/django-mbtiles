import os
from distutils.core import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='django-mbtiles',
    version='1.0',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    url='https://github.com/makinacorpus/django-mbtiles',
    description="Serve maps from MBTiles files",
    long_description=open(os.path.join(here, 'README.rst')).read(),
    requires = ['easydict (>=1.3)',
                'landez (>=1.6)'],
    packages=find_packages(),
    include_package_data=True,
    classifiers  = ['Topic :: Utilities', 
                    'Natural Language :: English',
                    'Operating System :: OS Independent',
                    'Intended Audience :: Developers',
                    'Environment :: Web Environment',
                    'Framework :: Django',
                    'Development Status :: 5 - Production/Stable',
                    'Programming Language :: Python :: 2.5'],
)
