# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Functie.models import Functie
from Mailer.models import MailQueue
from Taken.operations import (cached_aantal_open_taken, stuur_email_taak_herinnering, stuur_email_nieuwe_taak,
                              check_taak_bestaat, maak_taak, herinner_aan_taken)
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
import datetime


class TestTakenTaken(E2EHelpers, TestCase):

    """ tests voor de applicatie Taken """

    test_after = ('Functie',)

    emailadres = 'taak@test.not'
    emailadres2 = 'taak2@test.not'

    def setUp(self):
        """ initialisatie van de test case """

        self.functie_sup = Functie.objects.get(rol='SUP')
        self.functie_sup.bevestigde_email = self.emailadres
        self.functie_sup.laatste_email_over_taken = None
        self.functie_sup.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

        self.functie_mwz = Functie.objects.get(rol='MWZ')
        self.functie_mwz.bevestigde_email = ''
        self.functie_mwz.laatste_email_over_taken = None
        self.functie_mwz.save(update_fields=['bevestigde_email', 'laatste_email_over_taken'])

    def test_aantal_open_taken(self):
        # standaard sessie heeft nog geen opgeslagen aantal taken
        request = self.client
        aantal = cached_aantal_open_taken(request)
        self.assertEqual(aantal, 0)

    def test_stuur_email_taak_herinnering(self):
        self.assertEqual(0, MailQueue.objects.count())
        stuur_email_taak_herinnering(self.emailadres, 1)     # 1 taak
        self.assertEqual(1, MailQueue.objects.count())

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_taken/herinnering.dtl')
        self.assert_consistent_email_html_text(mail)

        stuur_email_taak_herinnering(self.emailadres, 5)     # 5 taken
        self.assertEqual(2, MailQueue.objects.count())

    def test_stuur_email_nieuwe_taak(self):
        self.assertEqual(0, MailQueue.objects.count())
        stuur_email_nieuwe_taak(self.emailadres, 'test', 1)         # 1 taak
        self.assertEqual(1, MailQueue.objects.count())

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_taken/nieuwe_taak.dtl')
        self.assert_consistent_email_html_text(mail)

        stuur_email_nieuwe_taak(self.emailadres, 'test', 2)         # 2 taken
        self.assertEqual(2, MailQueue.objects.count())

    def test_maak_taak(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        deadline = datetime.date(2020, 12, 13)

        bestaat = check_taak_bestaat(deadline=deadline)
        self.assertFalse(bestaat)

        bestaat = check_taak_bestaat(skip_afgerond=False, deadline=deadline)
        self.assertFalse(bestaat)

        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst",
            log="Log")

        self.assertEqual(1, Taak.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        bestaat = check_taak_bestaat(deadline=deadline)
        self.assertTrue(bestaat)

        taak = Taak.objects.first()
        self.assertFalse(taak.is_afgerond)
        self.assertEqual(taak.toegekend_aan_functie, self.functie_sup)
        self.assertEqual(taak.deadline, deadline)
        self.assertEqual(taak.aangemaakt_door, None)
        self.assertEqual(taak.beschrijving, "Tekst")
        self.assertEqual(taak.log, "Log")

        mail = MailQueue.objects.first()
        self.assertFalse(mail.is_verstuurd)
        self.assertEqual(mail.aantal_pogingen, 0)
        self.assertEqual(mail.mail_to, self.emailadres)

        # extra coverage
        self.assertTrue(str(taak) != "")
        taak.is_afgerond = True
        self.assertTrue(str(taak) != "")

        # maak nog een taak en controleer dat er weer meteen een email uit gaat
        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst 2",
            log="Log 2")

        self.assertEqual(2, Taak.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

    def test_taak_geen_email(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        deadline = datetime.date(2020, 12, 14)

        maak_taak(
            toegekend_aan_functie=self.functie_mwz,         # heeft geen emailadres
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst2",
            log="Log")

        self.assertEqual(1, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())      # want: geen emailadres

        taak = Taak.objects.first()
        self.assertFalse(taak.is_afgerond)
        self.assertEqual(taak.toegekend_aan_functie, self.functie_mwz)
        self.assertEqual(taak.deadline, deadline)
        self.assertEqual(taak.aangemaakt_door, None)
        self.assertEqual(taak.beschrijving, "Tekst2")
        self.assertEqual(taak.log, "Log")

    def test_optout_nieuw(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        self.functie_sup.optout_nieuwe_taak = True
        self.functie_sup.save(update_fields=['optout_nieuwe_taak'])

        # maak een taak aan en controleer dat er geen mail uit gaat, want: opt-out
        deadline = datetime.date(2020, 12, 13)
        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst",
            log="Log")

        self.assertEqual(1, Taak.objects.count())           # taak is aangemaakt
        self.assertEqual(0, MailQueue.objects.count())      # maar mail is er niet uit gegaan

        # controleer dat alle velden van de taak goed ingevuld zijn
        taak = Taak.objects.first()
        self.assertFalse(taak.is_afgerond)
        self.assertEqual(taak.toegekend_aan_functie, self.functie_sup)
        self.assertEqual(taak.deadline, deadline)
        self.assertEqual(taak.aangemaakt_door, None)
        self.assertEqual(taak.beschrijving, "Tekst")
        self.assertEqual(taak.log, "Log")

    def test_optout_herinner(self):
        self.assertEqual(0, Taak.objects.count())

        self.functie_sup.optout_herinnering_taken = True
        self.functie_sup.save(update_fields=['optout_herinnering_taken'])

        # maak een taak aan
        deadline = datetime.date(2020, 12, 13)
        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst",
            log="Log")

        self.assertEqual(1, Taak.objects.count())           # taak is aangemaakt

        MailQueue.objects.all().delete()
        self.assertEqual(0, MailQueue.objects.count())      # maar mail is er niet uit gegaan

        # controleer dat er geen herinneringsmail uit gaat
        herinner_aan_taken()
        self.assertEqual(0, MailQueue.objects.count())      # maar mail is er niet uit gegaan

    def test_herinner_aan_taken(self):

        self.functie_mwz.bevestigde_email = self.emailadres2
        self.functie_mwz.save(update_fields=['bevestigde_email'])

        deadline = datetime.date(2000, 1, 1)

        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        # maak 3 taken aan voor 2 functies
        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            beschrijving="Tekst 1")

        maak_taak(
            toegekend_aan_functie=self.functie_sup,
            deadline=deadline,
            beschrijving="Tekst 2")

        maak_taak(
            toegekend_aan_functie=self.functie_mwz,
            deadline=deadline,
            beschrijving="Tekst 3")

        self.assertEqual(3, Taak.objects.count())
        self.assertEqual(3, MailQueue.objects.count())

        # bij het aanmaken van de taken is laatste_email_over_taken gezet
        # dus er worden geen herinneringen gestuurd
        herinner_aan_taken()
        self.assertEqual(3, MailQueue.objects.count())

        self.functie_mwz = Functie.objects.get(pk=self.functie_mwz.pk)
        self.functie_sup = Functie.objects.get(pk=self.functie_sup.pk)
        self.assertIsNotNone(self.functie_mwz.laatste_email_over_taken)
        self.assertIsNotNone(self.functie_sup.laatste_email_over_taken)

        # controleer dat de herinnering pas gestuurd worden na 7 dagen
        self.functie_mwz.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) + datetime.timedelta(hours=1)
        self.functie_mwz.save(update_fields=['laatste_email_over_taken'])
        herinner_aan_taken()
        self.assertEqual(3, MailQueue.objects.count())

        self.functie_mwz.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) - datetime.timedelta(hours=1)
        self.functie_mwz.save(update_fields=['laatste_email_over_taken'])
        herinner_aan_taken()
        self.assertEqual(4, MailQueue.objects.count())

        # corner case
        self.functie_mwz.laatste_email_over_taken = None
        self.functie_mwz.save(update_fields=['laatste_email_over_taken'])
        herinner_aan_taken()
        self.assertEqual(5, MailQueue.objects.count())

# end of file
