#!/bin/bash

mkdir -p /run/php

php-fpm7.0 -R
nginx -g 'daemon off;'
