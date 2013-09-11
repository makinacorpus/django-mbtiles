FROM makinacorpus/pythonbox
MAINTAINER Mathieu Leplatre "mathieu.leplatre@makina-corpus.com"

RUN apt-get install -y git nginx

RUN mkdir -p /data/makinacorpus
ENV MBTILES_ROOT /data/makinacorpus

ADD . /opt/apps/livembtiles
RUN (cd /opt/apps/livembtiles && git remote rm origin)
RUN (cd /opt/apps/livembtiles && git remote add origin https://github.com/makinacorpus/django-mbtiles.git)
RUN (cd /opt/apps/livembtiles && make install deploy)
RUN /opt/apps/livembtiles/bin/pip install uwsgi

ADD .docker/run.sh /usr/local/bin/run
ADD .docker/nginx.conf /etc/nginx/sites-available/default

#
#  Run !
#...
EXPOSE 80
CMD ["/bin/sh", "-e", "/usr/local/bin/run"]