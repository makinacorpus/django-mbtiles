install: bin/python

bin/python:
	virtualenv .
	wget http://svn.zope.org/repos/main/zc.buildout/branches/1.4/bootstrap/bootstrap.py 
	bin/python bootstrap.py --version=1.4.4
	bin/buildout -Nvc buildout.cfg
	rm bootstrap.py

serve: bin/python
	bin/django runserver

clean:
	rm -rf bin/ lib/ *.egg-info/ include/ local/ .installed.cfg

