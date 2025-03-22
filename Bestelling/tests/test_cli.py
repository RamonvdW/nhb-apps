# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestelling.definities import (BESTELLING_REGEL_CODE_WEBWINKEL,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_EVENEMENT,
                                   BESTELLING_REGEL_CODE_OPLEIDING,
                                   BESTELLING_REGEL_CODE_VERZENDKOSTEN,
                                   BESTELLING_MUTATIE_VERWIJDER,
                                   BESTELLING_MUTATIE_TRANSPORT)
from Bestelling.models import BestellingMandje, Bestelling, BestellingRegel, BestellingMutatie
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from decimal import Decimal
import datetime
import time


class TestBestellingCli(E2EHelpers, TestCase):

    """ unittests voor de Bestelling applicatie, command line interfaces """

    def setUp(self):
        """ initialisatie van de test case """

        self.account = self.e2e_create_account_admin()

        mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account)
        self.mandje = mandje

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112),
                    bank_iban='IBAN123456789',
                    bank_bic='BIC2BIC',
                    kvk_nummer='KvK1234',
                    website='www.bb.not',
                    contact_email='info@bb.not',
                    telefoonnummer='12345678')
        ver.save()
        self.ver = ver

        instelling = BetaalInstellingenVereniging(
                        vereniging=ver,
                        mollie_api_key='Test')
        instelling.save()
        self.instelling = instelling

        hwl = Functie(
                beschrijving='HWL 1000',
                rol='HWL',
                bevestigde_email='hwl@ver1000.not',
                vereniging=self.ver)
        hwl.save()

    def test_stuur_overboeken_herinneringen(self):
        now = timezone.now()
        verleden = now - datetime.timedelta(days=1 + settings.MANDJE_VERVAL_NA_DAGEN)

        regel1 = BestellingRegel(
                        korte_beschrijving='webwinkel',
                        bedrag_euro=Decimal('1.23'),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel1.save()

        regel2 = BestellingRegel(
                        korte_beschrijving='wedstrijd',
                        bedrag_euro=Decimal('10.00'),
                        code=BESTELLING_REGEL_CODE_WEDSTRIJD)
        regel2.save()

        regel3 = BestellingRegel(
                        korte_beschrijving='evenement',
                        bedrag_euro=Decimal('15.00'),
                        code=BESTELLING_REGEL_CODE_EVENEMENT)
        regel3.save()

        regel4 = BestellingRegel(
                        korte_beschrijving='opleiding',
                        bedrag_euro=Decimal('42.00'),
                        code=BESTELLING_REGEL_CODE_OPLEIDING)
        regel4.save()

        regel5 = BestellingRegel(
                        korte_beschrijving='verzendkosten',
                        bedrag_euro=Decimal('6.95'),
                        code=BESTELLING_REGEL_CODE_VERZENDKOSTEN)
        regel5.save()

        # zet het mandje om in een bestelling
        bestelling = Bestelling(
                        bestel_nr=42,
                        account=self.account,
                        ontvanger=self.instelling)
        bestelling.save()
        bestelling.aangemaakt -= datetime.timedelta(days=5)
        bestelling.save(update_fields=['aangemaakt'])

        bestelling.regels.add(regel1, regel2, regel3, regel4, regel5)

        self.assertEqual(0, Taak.objects.count())
        with self.assert_max_queries(20):
            f1, f2, = self.run_management_command('stuur_overboeken_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(' 1 onbetaalde bestellingen voor vereniging [1000] Grote Club' in f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

        # nog een keer; controleer dat geen nieuwe taak aangemaakt wordt
        f1, f2, = self.run_management_command('stuur_overboeken_herinneringen')
        self.assertTrue(' 1 onbetaalde bestellingen voor vereniging [1000] Grote Club' in f2.getvalue())
        self.assertEqual(1, Taak.objects.count())

    def test_mandje_herinneringen(self):
        # leg product in mandje
        regel1 = BestellingRegel(
                        korte_beschrijving='webwinkel',
                        bedrag_euro=Decimal('1.23'),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel1.save()
        self.mandje.regels.add(regel1)

        self.assertEqual(MailQueue.objects.count(), 0)

        f1, f2 = self.run_management_command('stuur_mandje_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[INFO] Mandje met producten: 424242' in f2.getvalue())     # 424242 == self.account.username

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/herinnering-mandje.dtl')
        self.assert_consistent_email_html_text(mail)
        self.assertTrue('1 product ' in mail.mail_text)
        mail.delete()

        # leg 2e product in mandje
        regel2 = BestellingRegel(
                        korte_beschrijving='webwinkel2',
                        bedrag_euro=Decimal('42.00'),
                        code=BESTELLING_REGEL_CODE_WEBWINKEL)
        regel2.save()
        self.mandje.regels.add(regel2)

        f1, f2 = self.run_management_command('stuur_mandje_herinneringen')
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue('[INFO] Mandje met producten: 424242' in f2.getvalue())     # 424242 == self.account.username

        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/herinnering-mandje.dtl')
        self.assert_consistent_email_html_text(mail)
        self.assertTrue('2 producten ' in mail.mail_text)
        mail.delete()

    def test_mutatie(self):

        # geen werk
        BestellingMutatie.objects.all().delete()
        BestellingMutatie(code=BESTELLING_MUTATIE_TRANSPORT, is_verwerkt=True).save()       # al verwerkt
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick')
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())

        BestellingMutatie(code=9999).save()                                                 # onbekende mutatie
        f1, f2 = self.run_management_command('bestel_mutaties', '60', '--quick')            # 60 == fake-hoogste
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('[INFO] vorige hoogste BestellingMutatie pk is 0' in f2.getvalue())
        self.assertTrue('[ERROR] Onbekende mutatie code 9999' in f2.getvalue())

        # trigger een exceptie
        BestellingMutatie(code=BESTELLING_MUTATIE_VERWIJDER).save()
        f1, f2 = self.run_management_command('bestel_mutaties', '60', '--quick')
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('Traceback:' in f1.getvalue())
        BestellingMutatie.objects.all().delete()

        # test "stop exactly"
        now = datetime.datetime.now()
        if now.second > 55:                             # pragma: no cover
            print('Waiting until clock is past xx:xx:59')
            while now.second > 55:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        now = datetime.datetime.now()
        if now.minute == 0:                             # pragma: no cover
            print('Waiting until clock is past xx:00')
            while now.minute == 0:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the current minute
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % now.minute)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        # trigger the negative case
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute - 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        now = datetime.datetime.now()
        if now.minute == 59:                             # pragma: no cover
            print('Waiting until clock is past xx:59')
            while now.minute == 59:
                time.sleep(5)
                now = datetime.datetime.now()
            # while

        # trigger the positive case
        f1, f2 = self.run_management_command('bestel_mutaties', '1', '--quick',
                                             '--stop_exactly=%s' % (now.minute + 1))
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

# end of file
