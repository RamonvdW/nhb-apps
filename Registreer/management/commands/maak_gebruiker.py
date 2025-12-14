# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een gebruiker (sporter + account + sportersboog) aan vanaf de commandline
# dit is bedoeld voor demonstraties en de handleiding

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from django.utils import timezone
from Account.models import Account
from Account.operations import account_create
from BasisTypen.models import BoogType
from Sporter.models import Sporter, SporterBoog
from Vereniging.models import Vereniging
from random import random


class Command(BaseCommand):
    help = "Voeg een sporter lid toe en maak een account aan"

    def add_arguments(self, parser):
        parser.add_argument('ver_nr', nargs=1)
        parser.add_argument('lid_nr', nargs=1)
        parser.add_argument('voornaam', nargs=1)
        parser.add_argument('geboorte_datum', nargs=1, help="yyyy-mm-dd")
        parser.add_argument('wedstrijdbogen', nargs=1, help="R,C,BB,etc. Meerdere: R+C")

    def handle(self, *args, **options):
        ver_nr = options['ver_nr'][0]
        lid_nr = options['lid_nr'][0]
        voornaam = options['voornaam'][0].replace(' ', '-')
        achternaam = 'van de Demo'
        email = voornaam.lower() + '@demo.it'
        password = str(random())[2:2+10]
        geboorte_datum = options['geboorte_datum'][0]
        wedstrijdbogen = options['wedstrijdbogen'][0].split('+')

        try:
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            self.stderr.write('[ERROR] Vereniging %s niet gevonden' % ver_nr)
            return

        self.stdout.write('[INFO] Maak of vind account %s' % lid_nr)

        try:
            account = Account.objects.get(username=lid_nr)
        except Account.DoesNotExist:
            account = account_create(lid_nr, voornaam, achternaam, password, email, True)

        self.stdout.write('[INFO] Maak sporter %s' % lid_nr)

        try:
            sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            sporter = Sporter(
                        lid_nr=lid_nr,
                        voornaam=voornaam,
                        achternaam=achternaam,
                        unaccented_naam=voornaam + ' ' + achternaam,
                        email=email,
                        geboorte_datum=geboorte_datum,
                        geboorteplaats='Pijlstad',
                        geslacht="M",
                        adres_code=geboorte_datum.replace('-', '')[-4:] + 'ZZ',     # maak maand + dag
                        sinds_datum=timezone.now().date(),
                        bij_vereniging=ver,
                        lid_tot_einde_jaar=timezone.now().year,
                        account=account)
            sporter.save()

        for wedstrijdboog in wedstrijdbogen:
            self.stdout.write('[INFO] Maak sporterboog voor boog %s' % wedstrijdboog)

            boogtype = BoogType.objects.get(afkorting=wedstrijdboog)

            sporterboog = SporterBoog(
                                sporter=sporter,
                                boogtype=boogtype,
                                voor_wedstrijd=True)

            try:
                sporterboog.save()
            except IntegrityError:      # pragma: no cover
                pass
        # for

# end of file
