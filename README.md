# Odoo HA + Load Balancing + uWSGI + Nginx Deploy

Some people when deploying Odoo do so by the simple route of running `odoo-bin`, which does not allow for having an infrastructure deployed to balance the load between several of these servers. One of the problems is the storage of the user's session data, which by default is written into the Odoo data folder, invalidating the possibility of load balancing between 2 (or more) because the sessions would not be found between them.

I created this repository to provide a Dockerfile prepared with Odoo 13 with these characteristics:

* It uses uWSGI to run Odoo, with automatic scaling of the workers.
* It uses NGINX as a reverse proxy to connect to the uWSGI using its own protocol and through a UNIX socket.
* It provides the module statics directly from NGINX without going through Odoo.
* NGINX has support for brotli and gzip, considerably reducing the load wait for clients.
* Use a module that add Redis support to store HTTP Sessions.
* Use a module that allow save the attachments to PostgreSQL using Large Object.
* A Monkey Patch is applied to Odoo to be executed using Gevents, which increases its performance with less resource consumption.

Details to be taken into account:

* When Odoo runs with uWSGI it doesn't raise the LongPolling and Cron service, the image is prepared to be run separately (at least 1) with the environment variable `ODOO_MODE=longpoll-cron` which tells it to run only the LongPolling and Cron.
* To install new modules it is advisable to use the environment variables in a new image `ODOO_MODE=install-update-modules` together with `MODULES_TO_INSTALL=modulo1,modulo2,modulo3...`.

# How to build

Simple, use the `docker build` command.

# How to run

The entrypoint of this image use some enviroment variables:

Variable     | Description
--------     | -----------
`DB_NAME`    | Database name
`DB_USER`    | Database username
`DB_PASS`    | Database password
`DB_HOST`    | Database host
`DB_PORT`    | Database port
`REDIS_HOST` | Redis Host
`REDIS_PORT` | Redis Port

`ODOO_MODE`  | Image start mode

`MODULES_TO_INSTALL` | Modules to install on `install-update-modules` mode

The image start mode can be:
* `longpoll-cron`: Init the Long Polling + Cron of Odoo.
* `install-update-modules`: Install the modules defined in `MODULES_TO_INSTALL`
* `uwsgi-server`: Init uWSGI + Nginx to serve

If you want add custom modules, Odoo is configured to search on `/usr/src/app/extra-modules`, you can mount a volume inside it.

# Resources from where I was based this work

* https://github.com/odexperts/odoo-cloud
* https://github.com/camptocamp/odoo-cloud-platform
