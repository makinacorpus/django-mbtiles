#!/usr/bin/python
# -*- coding: utf8 -*-
import os
from distutils.core import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(
    name='livembtiles',
    version='1.0',
    author='Mathieu Leplatre',
    author_email='mathieu.leplatre@makina-corpus.com',
    url='https://github.com/makinacorpus/django-mbtiles',
    description="Map browser as an example project for django-mbtiles.",
    long_description=open(os.path.join(here, 'README.rst')).read(),
    requires = ['django_mbtiles (==1.0)'],
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
