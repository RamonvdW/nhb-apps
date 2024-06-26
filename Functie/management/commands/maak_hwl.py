# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

# maak een account HWL van specifieke vereniging, vanaf de commandline

from django.core.management.base import BaseCommand
from Account.models import Account
from Functie.models import Functie
from Logboek.models import schrijf_in_logboek
from Vereniging.models import Vereniging


class Command(BaseCommand):
    help = "Maak account HWL voor specifieke vereniging"

    def add_arguments(self, parser):
        parser.add_argument('username', nargs=1, help="inlog naam")
        parser.add_argument('ver_nr', nargs=1, help='Verenigingsnummer')

    def get_account(self, username):
        try:
            account = Account.objects.get(username=username)
        except Account.DoesNotExist:
            self.stderr.write("[ERROR] Kan account %s niet vinden" % username)
            account = None
        return account

    def get_vereniging(self, ver_nr):
        try:
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            self.stderr.write("[ERROR] Kan vereniging %s niet vinden" % ver_nr)
            ver = None
        return ver

    def get_functie_hwl(self, ver):
        try:
            functie = Functie.objects.get(rol='HWL', vereniging=ver)
        except Functie.DoesNotExist:
            self.stderr.write("[ERROR] Kan HWL functie van vereniging %s niet vinden" % ver.ver_nr)
            functie = None
        return functie

    def handle(self, *args, **options):
        username = options['username'][0]
        account = self.get_account(username)

        ver_nr = options['ver_nr'][0]
        ver = self.get_vereniging(ver_nr)

        activiteit = ""
        if account and ver:
            functie = self.get_functie_hwl(ver)

            if functie:
                if functie.accounts.filter(pk=account.pk).count():
                    self.stdout.write('[WARNING] Account %s is al HWL van vereniging %s' % (repr(username), ver))
                else:
                    # maak dit account HWL
                    functie.accounts.add(account)

                    activiteit = "Account %s is HWL gemaakt van vereniging %s" % (repr(username), ver)

                    # schrijf in het logboek
                    schrijf_in_logboek(account=None,
                                       gebruikte_functie='maak_hwl (command line)',
                                       activiteit=activiteit)
                    self.stdout.write(activiteit)

        if not activiteit:
            self.stderr.write('[ERROR] Kon account %s geen HWL maken van vereniging %s' % (username, ver_nr))

# end of file
