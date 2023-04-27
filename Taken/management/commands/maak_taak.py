# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een taak aan voor een specifieke gebruiker

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from Account.models import Account
from Functie.models import Functie
from Taken.models import Taak


class Command(BaseCommand):
    help = "Maak een taak aan"
    verbose = False

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self._beheerder_accounts = list()

    def add_arguments(self, parser):
        parser.add_argument('toekennen_aan', nargs=1, help="Functie beschrijving (deel van)")
        parser.add_argument('aangemaakt_door', nargs=1, help="Account inlog naam of 'systeem'")
        parser.add_argument('deadline', nargs=1, help='Wanneer moet het af zijn (formaat: YYYY-MM-DD)')
        parser.add_argument('beschrijving', nargs=1, help='Beschrijving (gebruik \\n voor nieuwe regel)')

    def handle(self, *args, **options):

        toekennen_aan = options['toekennen_aan'][0]

        qset = Functie.objects.filter(Q(beschrijving__icontains=toekennen_aan) | Q(rol=toekennen_aan))
        functie_count = qset.count()

        if functie_count == 0:
            self.stderr.write('[ERROR] Geen functie gevonden die voldoet aan %s' % repr(toekennen_aan))
            return

        if functie_count > 1:
            self.stderr.write('[ERROR] Meerdere functies gevonden die voldoen aan %s' % repr(toekennen_aan))
            for functie in qset:
                self.stderr.write('    (%s) %s' % (functie.rol, functie.beschrijving))
            # for
            return

        toekennen_aan_functie = qset[0]
        self.stdout.write('[INFO] Gekozen functie: %s' % toekennen_aan_functie)

        if not toekennen_aan_functie.bevestigde_email:
            self.stdout.write('[WARNING] Geen e-mailadres bekend voor functie %s' % toekennen_aan_functie)

        aangemaakt_door = options['aangemaakt_door'][0]
        if aangemaakt_door.lower() in ('systeem', '', 'none'):
            aangemaakt_door_account = None
        else:
            try:
                aangemaakt_door_account = Account.objects.get(username=aangemaakt_door)
            except Account.DoesNotExist as exc:
                self.stderr.write("%s" % str(exc))
                return

        deadline = options['deadline'][0]
        beschrijving = options['beschrijving'][0].replace('\\n', '\n')

        log = "[%s] Taak gemaakt via de cli\n" % timezone.now().strftime('%Y-%m-%d om %H:%M')

        taak = Taak(aangemaakt_door=aangemaakt_door_account,
                    toegekend_aan_functie=toekennen_aan_functie,
                    deadline=deadline,
                    beschrijving=beschrijving,
                    log=log)
        taak.save()

        if not taak.aangemaakt_door:
            door_str = 'Systeem'
        else:
            door_str = taak.aangemaakt_door.username

        self.stdout.write('Taak aangemaakt door %s voor functie %s met deadline %s' % (door_str,
                                                                                       taak.toegekend_aan_functie,
                                                                                       taak.deadline))

# end of file
