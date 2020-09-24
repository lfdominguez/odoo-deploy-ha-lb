#!/usr/bin/env python3

import gevent.monkey
gevent.monkey.patch_all()

# set server timezone in UTC before time module imported
__import__('os').environ['TZ'] = 'UTC'
import odoo

if __name__ == "__main__":
    odoo.cli.main()
    
