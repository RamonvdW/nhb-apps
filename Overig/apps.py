# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import AppConfig
from django.utils.autoreload import autoreload_started
import sys
import os


def my_watchdog_dtl(sender, **kwargs):
    """ Deze functie wordt aangeroepen als de auto reloader gestart is
        We vragen om de .dtl files van alle applicaties te monitoren
    """
    for root, dirs, files in os.walk('.'):
        if '/templates/' in root:
            print('Watching %s/*.dtl' % root)
            sender.watch_dir(root, '*.dtl')


class OverigConfig(AppConfig):
    name = 'Overig'

    def ready(self):
        if 'runserver' in sys.argv:
            # very likely started with ./manage.py runserver
            # monitor for .dtl file changes
            autoreload_started.connect(my_watchdog_dtl)

# end of file
