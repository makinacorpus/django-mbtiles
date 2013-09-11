#!/bin/bash
SECRET_KEY=${SECRET_KEY:-paranoid}
ALLOWED_HOSTS=${ALLOWED_HOSTS:-*}
DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-livembtiles.settings}
MBTILES_ROOT=${MBTILES_ROOT}

APP_ROOT=/opt/apps/livembtiles
BRANCH=livembtiles
WSGI=livembtiles.wsgi



cd $APP_ROOT
git pull origin $BRANCH

bin/uwsgi \
    --http-socket 0.0.0.0:8000 \
    --processes 4 \
    --buffer-size 32768 \
    --enable-threads \
    --master \
    --max-requests 5000 \
    --virtualenv $APP_ROOT \
    --module $WSGI