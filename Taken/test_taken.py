# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Mailer.models import MailQueue
from Sporter.models import Sporter
from Taken.operations import (aantal_open_taken, stuur_taak_email_herinnering, stuur_nieuwe_taak_email,
                              check_taak_bestaat, maak_taak, herinner_aan_taken)
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata
import datetime


class TestTakenTaken(E2EHelpers, TestCase):

    """ tests voor de applicatie Taken """

    test_after = ('Functie',)

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def setUp(self):
        """ initialisatie van de test case """

        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_same = self.e2e_create_account('same', 'same@test.com', 'same')

        sporter = Sporter()
        sporter.lid_nr = 100042
        sporter.geslacht = "M"
        sporter.voornaam = "Beh"
        sporter.achternaam = "eerder"
        sporter.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        sporter.sinds_datum = datetime.date(year=2010, month=11, day=12)
        sporter.account = self.account_normaal
        sporter.email = sporter.account.email
        sporter.save()

    def test_aantal_open_taken(self):
        # standaard sessie heeft nog geen opgeslagen aantal taken
        request = self.client
        aantal = aantal_open_taken(request)
        self.assertIsNone(aantal)

    def test_stuur_taak_email_herinnering(self):
        self.assertEqual(0, MailQueue.objects.count())
        email = self.account_normaal.accountemail_set.all()[0]
        stuur_taak_email_herinnering(email, 5)

        # er moet nu een mail in de MailQueue staan
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail.mail_html, 'email_taken/herinnering.dtl')

    def test_stuur_nieuwe_taak_email(self):
        self.assertEqual(0, MailQueue.objects.count())
        email = self.account_normaal.accountemail_set.all()[0]
        stuur_nieuwe_taak_email(email, 5)
        self.assertEqual(1, MailQueue.objects.count())

        # er moet nu een mail in de MailQueue staan
        self.assertEqual(MailQueue.objects.count(), 1)
        mail = MailQueue.objects.all()[0]
        self.assert_email_html_ok(mail.mail_html, 'email_taken/nieuwe_taak.dtl')

    def test_maak_taak(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        deadline = datetime.date(2020, 12, 13)

        bestaat = check_taak_bestaat(deadline=deadline)
        self.assertFalse(bestaat)

        maak_taak(
            toegekend_aan=self.account_normaal,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst",
            handleiding_pagina="Pagina",
            log="Log")

        self.assertEqual(1, Taak.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

        bestaat = check_taak_bestaat(deadline=deadline)
        self.assertTrue(bestaat)

        taak = Taak.objects.all()[0]
        self.assertFalse(taak.is_afgerond)
        self.assertEqual(taak.toegekend_aan, self.account_normaal)
        self.assertEqual(taak.deadline, deadline)
        self.assertEqual(taak.aangemaakt_door, None)
        self.assertEqual(taak.beschrijving, "Tekst")
        self.assertEqual(taak.handleiding_pagina, "Pagina")
        self.assertEqual(taak.log, "Log")
        self.assertEqual(taak.deelcompetitie, None)

        mail = MailQueue.objects.all()[0]
        self.assertFalse(mail.is_verstuurd)
        self.assertEqual(mail.aantal_pogingen, 0)
        self.assertEqual(mail.mail_to, 'normaal@test.com')

        # extra coverage
        self.assertTrue(str(taak) != "")
        taak.is_afgerond = True
        self.assertTrue(str(taak) != "")

        # maak nog een taak en controleer dat er weer meteen een email uit gaat
        maak_taak(
            toegekend_aan=self.account_normaal,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst 2",
            handleiding_pagina="Pagina 2",
            log="Log 2")

        self.assertEqual(2, Taak.objects.count())
        self.assertEqual(2, MailQueue.objects.count())

    def test_maak_taak_optout(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        deadline = datetime.date(2020, 12, 13)

        # maak een taak aan en controleer dat er geen mail uit gaat, want: opt-out
        email = self.account_normaal.accountemail_set.all()[0]
        email.optout_nieuwe_taak = True
        email.save()
        maak_taak(
            toegekend_aan=self.account_normaal,
            deadline=deadline,
            aangemaakt_door=None,
            beschrijving="Tekst",
            handleiding_pagina="Pagina",
            log="Log")

        self.assertEqual(1, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        # controleer dat alle velden van de taak goed ingevuld zijn
        taak = Taak.objects.all()[0]
        self.assertFalse(taak.is_afgerond)
        self.assertEqual(taak.toegekend_aan, self.account_normaal)
        self.assertEqual(taak.deadline, deadline)
        self.assertEqual(taak.aangemaakt_door, None)
        self.assertEqual(taak.beschrijving, "Tekst")
        self.assertEqual(taak.handleiding_pagina, "Pagina")
        self.assertEqual(taak.log, "Log")
        self.assertEqual(taak.deelcompetitie, None)

        # controleer dat de herinnering geen mail stuurt na opt-out
        email.optout_nieuwe_taak = False
        email.optout_herinnering_taken = True
        email.save()
        herinner_aan_taken()
        self.assertEqual(0, MailQueue.objects.count())

    def test_herinner_aan_taken(self):

        deadline = datetime.date(2000, 1, 1)

        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        # maak 3 taken aan voor 2 accounts
        maak_taak(
            toegekend_aan=self.account_normaal,
            deadline=deadline,
            beschrijving="Tekst 1")

        maak_taak(
            toegekend_aan=self.account_normaal,
            deadline=deadline,
            beschrijving="Tekst 2")

        maak_taak(
            toegekend_aan=self.testdata.account_admin,
            deadline=deadline,
            beschrijving="Tekst 3")

        self.assertEqual(3, Taak.objects.count())
        self.assertEqual(3, MailQueue.objects.count())

        # vraag nu om herinneringen te sturen
        email = self.testdata.account_admin.accountemail_set.all()[0]
        email.laatste_email_over_taken = None
        email.save()

        herinner_aan_taken()
        self.assertEqual(4, MailQueue.objects.count())

        # controleer dat de herinnering pas gestuurd worden na 7 dagen
        email.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) + datetime.timedelta(hours=1)
        email.save()

        herinner_aan_taken()
        self.assertEqual(4, MailQueue.objects.count())

        email.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) - datetime.timedelta(hours=1)
        email.save()

        herinner_aan_taken()
        self.assertEqual(5, MailQueue.objects.count())

# end of file
