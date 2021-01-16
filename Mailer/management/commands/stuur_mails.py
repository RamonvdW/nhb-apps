# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" dit commando probeert een aantal mail te versturen
    normaal gebruik is aanroep vanuit een cron-job, typisch elke 5 minuten
"""

from Mailer import mailer
from Mailer.models import MailQueue
from Taken.taken import herinner_aan_taken
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.utils import DataError
import datetime
import time


class Command(BaseCommand):

    help = "Probeer een aantal mails te sturen die in de queue staan"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.stop_at = 0

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing
        parser.add_argument('--skip_old', action='store_true')  # for testing

    def _cleanout_old_blocked_mails(self):
        one_month_ago = timezone.now() - datetime.timedelta(days=31)
        objs = (MailQueue
                .objects
                .filter(toegevoegd_op__lt=one_month_ago,
                        is_blocked=True))
        self.stdout.write('[DEBUG] Could delete %s old blocked mails' % len(objs))
        # TODO: actually delete old blocked mails

    def _stuur_oude_mails(self):
        # probeer eenmalig oude mails te sturen en keer daarna terug
        send_count = 0
        for obj in (MailQueue
                    .objects
                    .filter(is_verstuurd=False,
                            is_blocked=False,
                            aantal_pogingen__lt=25)):
            mailer.send_mail(obj, self.stdout, self.stderr)
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

            objs = (MailQueue
                    .objects
                    .filter(is_verstuurd=False,
                            is_blocked=False,
                            aantal_pogingen=0))
            if len(objs):
                obj = objs[0]
                mailer.send_mail(obj, self.stdout, self.stderr)
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

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=15))

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):
        self._set_stop_time(**options)

        # verwijder oude geblokkeerde mails
        self._cleanout_old_blocked_mails()

        # vang generieke fouten af
        try:
            herinner_aan_taken()
            if not options['skip_old']:
                self._stuur_oude_mails()
            self._stuur_nieuwe_mails()
        except DataError as exc:                        # pragma: no coverage
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
        except KeyboardInterrupt:                       # pragma: no coverage
            pass

        self.stdout.write('Klaar')


# end of file
