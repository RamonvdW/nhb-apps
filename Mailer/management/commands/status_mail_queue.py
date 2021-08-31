# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" dit commando geeft een status overzichtje van de mail queue """

from Mailer.models import MailQueue
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Status van de mail queue"

    def handle(self, *args, **options):

        count = (MailQueue
                 .objects
                 .filter(is_verstuurd=False,
                         is_blocked=False,
                         aantal_pogingen__lt=25)
                 .count())

        self.stdout.write('MQ: %s' % count)


# end of file
