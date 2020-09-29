FROM debian:buster-slim AS nginx_build

RUN apt-get update && \
    apt-get install -y wget gnupg2 git \
    build-essential zlib1g-dev libpcre3 libpcre3-dev unzip uuid-dev
RUN apt-key adv --no-tty  --keyserver hkp://pool.sks-keyservers.net:80 --recv-keys 573BFD6B3D8FBC641079A6ABABF5BD827BD9BF62
RUN echo "deb-src http://nginx.org/packages/mainline/debian/ buster nginx" >> /etc/apt/sources.list

WORKDIR /tmp

ENV NGINX_BASE_VERSION 1.19.2
ENV NGINX_VERSION "1.19.2-1~buster"

RUN apt-get update && \
    apt-get build-dep -y nginx && \
    apt-get source nginx=${NGINX_VERSION}

RUN git clone --depth=1 --recurse-submodules https://github.com/google/ngx_brotli.git


RUN sed -i 's/--with-stream_ssl_preread_module/--with-stream_ssl_preread_module --add-module=\/tmp\/ngx_brotli/g' /tmp/nginx-${NGINX_BASE_VERSION}/debian/rules && \
    cd /tmp/nginx-${NGINX_BASE_VERSION} && dpkg-buildpackage -uc -b

RUN mv /tmp/nginx_${NGINX_VERSION}_amd64.deb /tmp/nginx.deb

#==================================================================================
#----------------------------------------------------------------------------------
#==================================================================================

FROM python:3.7-slim-buster AS python_wheel

# Set install dir
WORKDIR /usr/src/app

ADD https://nightly.odoo.com/13.0/nightly/src/odoo_13.0.latest.tar.gz ./odoo_13.0.latest.tar.gz

RUN tar -xf odoo_13.0.latest.tar.gz --no-same-owner requirements.txt \
  && rm odoo_13.0.latest.tar.gz \
COPY cloud_addons/requirements.txt ./cloud-requirements.txt

RUN set -x; \
  apt update \
  && apt install -y --no-install-recommends ca-certificates python-dev libsasl2-dev libldap2-dev libssl-dev gcc libpq-dev \
  && rm -rf /var/lib/apt/lists/* \
  && pip install wheel\
  && pip wheel -r requirements.txt --wheel-dir=wheels \
  && pip uninstall -y psycopg2 && pip wheel --wheel-dir=wheels --no-binary :all: psycopg2 \
  && pip wheel --wheel-dir=wheels psycogreen gevent uwsgi \
  && pip wheel --wheel-dir=wheels -r cloud-requirements.txt

#==================================================================================
#----------------------------------------------------------------------------------
#==================================================================================

FROM python:3.7-slim-buster

# Set install dir
WORKDIR /usr/src/app

ADD https://nightly.odoo.com/13.0/nightly/src/odoo_13.0.latest.tar.gz ./odoo_13.0.latest.tar.gz
COPY --from=0 /tmp/nginx.deb /tmp/nginx.deb

# Create odoo user and directories and set permissions
RUN useradd -ms /bin/bash odoo \
  && mkdir /etc/odoo /mnt/odoo /mnt/odoo/cloud_addons /mnt/odoo/data /usr/src/app/extra_addons /usr/src/app/scripts \
  && chown -R odoo:odoo /etc/odoo /mnt/odoo  /usr/src/app \
  && runuser -u odoo -- tar -xf odoo_13.0.latest.tar.gz --no-same-owner \
  && runuser -u odoo -- mv `find -maxdepth 1 -iname "odoo-*"` odoo \
  && rm odoo_13.0.latest.tar.gz

# Install Odoo dependencies and nginx
RUN cp odoo/requirements.txt .
COPY cloud_addons/requirements.txt ./cloud-requirements.txt

COPY --from=python_wheel /usr/src/app/wheels wheels

RUN set -x; \
  apt update \
  && apt install -y --no-install-recommends curl \
  && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.stretch_amd64.deb \
  && echo '7e35a63f9db14f93ec7feeb0fce76b30c08f2057 wkhtmltox.deb' | sha1sum -c - \
  && apt install -y --no-install-recommends ./wkhtmltox.deb ca-certificates /tmp/nginx.deb supervisor \
  && rm -rf /var/lib/apt/lists/* wkhtmltox.deb /tmp/nginx.deb \
  && pip install --no-index --find-links=wheels --no-cache-dir -r requirements.txt \
  #&& pip uninstall -y psycopg2 && pip install --no-binary :all: psycopg2 \
  && pip install --no-index --find-links=wheels psycogreen gevent uwsgi \
  && pip install --no-index --find-links=wheels --no-cache-dir -r cloud-requirements.txt \
  && pip cache purge
    
# Copy odoo source and config
#COPY odoo ./odoo
COPY cloud_addons /mnt/odoo/cloud_addons
COPY src/entrypoint.sh ./
COPY src/scripts ./scripts
COPY src/odoo.conf /etc/odoo/
ENV PATH="/usr/src/app/scripts:${PATH}"

COPY uwsgi/odoo-wsgi.py src/supervisor-services.conf ./
COPY src/odoo-bin.py ./odoo/
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Define runtime configuration
ENV ODOO_RC /etc/odoo/odoo.conf
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
CMD ["odoo"]