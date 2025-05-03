# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig
from django.utils.autoreload import autoreload_started
import sys
import os


def start_dev_watch(sender, **kwargs):      # pragma: no cover
    """ Wordt aangeroepen na elke reload
        Monitor bestanden om live-edits te ondersteunen in de dev omgeving
        Python modules worden standaard al gemonitord.
    """
    print('[INFO] Watching for template edits')
    for root, dirs, files in os.walk('.'):
        if '/templates/' in root:
            # print('Watching %s/*.dtl' % root)
            sender.watch_dir(root, '*.dtl')
        # elif '/js/' in root:
        #     print('Watching %s/*.js' % root)
        #     sender.watch_dir(root, '*.js')
    # for


class OverigConfig(AppConfig):
    name = 'Overig'

    def ready(self):
        # perform one-time startup logic
        if 'runserver' in sys.argv:     # pragma: no cover
            # very likely started with ./manage.py runserver
            # monitor for live edits
            autoreload_started.connect(start_dev_watch)


# end of file
