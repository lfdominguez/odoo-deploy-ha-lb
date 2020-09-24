# WSGI Handler sample configuration file.
#
# Change the appropriate settings below, in order to provide the parameters
# that would normally be passed in the command-line.
# (at least conf['addons_path'])
#
# For generic wsgi handlers a global application is defined.
# For uwsgi this should work:
#   $ uwsgi_python --http :9090 --pythonpath . --wsgi-file openerp-wsgi.py
#
# For gunicorn additional globals need to be defined in the Gunicorn section.
# Then the following command should run:
#   $ gunicorn odoo:service.wsgi_server.application -c openerp-wsgi.py

import gevent.monkey
gevent.monkey.patch_all()
#import psycogreen.gevent
#psycogreen.gevent.patch_psycopg()

import odoo
import os

#----------------------------------------------------------
# Common
#----------------------------------------------------------
odoo.multi_process = True # Nah!

# Equivalent of --load command-line option
odoo.conf.server_wide_modules = ['odoo_cloud', 'base', 'web']
conf = odoo.tools.config

# Path to the OpenERP Addons repository (comma-separated for
# multiple locations)

conf['addons_path'] = '/usr/src/app/odoo/odoo/addons,/mnt/odoo/cloud_addons,/mnt/odoo/extra_addons'
conf['list_db'] = False
conf['proxy_mode'] = True
conf['data_dir'] = '/mnt/odoo/data'

# Optional database config if not using local socket
conf['db_name'] = os.environ['DB_NAME']
conf['db_host'] = os.environ['DB_HOST']
conf['db_user'] = os.environ['DB_USER']
conf['db_port'] = os.environ['DB_PORT']
conf['db_password'] = os.environ['DB_PASS']

# Redis Config
conf['redis_host'] = os.environ['REDIS_HOST']
conf['redis_port'] = os.environ['REDIS_PORT']

#----------------------------------------------------------
# Generic WSGI handlers application
#----------------------------------------------------------
application = odoo.service.wsgi_server.application

odoo.service.server.load_server_wide_modules()

# Initialize DB
# python odoo-bin.py -d odoo -r odoo -w "*0d00*" --db_host=10.128.14.130 --no-http -i base,mail,web,odoo_cloud --stop-after-init --addons-path="/usr/src/app/odoo/odoo/addons,/mnt/odoo/cloud_addons"

# uWSGI
# uwsgi --uid 1000 -s /tmp/uwsgi.sock --wsgi-file /usr/src/app/odoo-wsgi.py --strict --master --enable-threads --vacuum --single-interpreter --die-on-term --need-app --reload-on-rss 3400 --max-requests 2000 --python-path odoo --cheaper-algo busyness --processes=50 --cheaper 4 --cheaper-initial 4 --harakiri 60
