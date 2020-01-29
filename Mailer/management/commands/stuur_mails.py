# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" dit commando probeert een aantal mail te versturen
    normaal gebruik is aanroep vanuit een cron-job, typisch elke 5 minuten
"""

from Mailer import mailer
from Mailer.models import MailQueue
from django.core.management.base import BaseCommand
from django.db.models import ProtectedError
import django.db.utils
import argparse
import datetime
import time


class Command(BaseCommand):

    help = "Probeer een aantal mails te sturen die in de queue staan"

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={0, 1, 3, 5, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")

    def _stuur_oude_mails(self):
        # probeer eenmalig oude mails te sturen en keer daarna terug
        send_count = 0
        now = datetime.datetime.now()
        for obj in MailQueue.objects.filter(is_verstuurd=False, aantal_pogingen__lt=25):
            mailer.send_mail(obj)
            send_count += 1

            # bail out when time's up
            now = datetime.datetime.now()
            if now > self.stop_at:
                break       # from the for
        # for
        self.stdout.write("[INFO] Aantal oude mails geprobeerd te versturen: %s" % send_count)

    def _stuur_nieuwe_mails(self):
        # monitor voor nieuwe mails en verstuur die
        send_count = 0
        now = datetime.datetime.now()
        while now < self.stop_at:

            objs = MailQueue.objects.filter(is_verstuurd=False, aantal_pogingen=0)
            if len(objs):
                obj = objs[0]
                mailer.send_mail(obj)
                send_count += 1
            else:
                # sleep a bit, then check again
                secs = (self.stop_at - now).total_seconds()
                if secs > 5.0:
                    secs = 5.0
                time.sleep(secs)

            now = datetime.datetime.now()
        # while
        self.stdout.write("[INFO] Aantal nieuwe mails geprobeerd te versturen: %s" % send_count)

    def handle(self, *args, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 30 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']
        if duration:
            self.stop_at = datetime.datetime.now() + datetime.timedelta(minutes=duration) - datetime.timedelta(seconds=30)
        else:
            # voor testen
            self.stop_at = datetime.datetime.now() + datetime.timedelta(seconds=2)
        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

        # vang generieke fouten af
        try:
            self._stuur_oude_mails()
            self._stuur_nieuwe_mails()
        except django.db.utils.DataError as exc:        # pragma: no coverage
            self.stderr.write('[ERROR] Overwachte database fout: %s' % str(exc))

        self.stdout.write('Klaar')


# end of file
