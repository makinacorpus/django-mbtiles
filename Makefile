install: bin/python

bin/python:
	virtualenv .
	bin/python setup.py develop

serve: bin/python
	bin/python ./manage.py runserver 8888

deploy: bin/python
	bin/python ./manage.py collectstatic --clear --noinput --verbosity=0
	touch livembtiles/wsgi.py  # trigger reload

clean:
	rm -rf bin/ lib/ build/ dist/ *.egg-info/ include/ local/
