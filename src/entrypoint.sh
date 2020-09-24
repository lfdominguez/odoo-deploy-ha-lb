#!/bin/bash
set -e

case $ODOO_MODE in
    longpoll-cron)
        cd odoo
        python odoo-bin.py gevent -d $DB_NAME -r $DB_USER -w "$DB_PASS" --db_host=$DB_HOST --http-interface=0.0.0.0 --longpolling-port=7070 --addons-path="/usr/src/app/odoo/odoo/addons,/mnt/odoo/cloud_addons" --proxy-mode --max-cron-threads=1 --redis-host
    ;;
    install-update-modules)
        cd odoo
        python odoo-bin.py -d $DB_NAME -r $DB_USER -w "$DB_PASS" --db_host=$DB_HOST --no-http -i $MODULES_TO_INSTALL --stop-after-init --addons-path="/usr/src/app/odoo/odoo/addons,/mnt/odoo/cloud_addons,/usr/src/app/extra-addons"
    ;;
    uwsgi-server)
        supervisord -c supervisor-services.conf
    ;;
    *)
        echo "Mode not selected, must be one of (longpoll-cron, install-update-modules, uwsgi-server)"
        exit 1
    ;;
esac

exit 0
