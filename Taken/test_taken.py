# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from NhbStructuur.models import NhbLid
from Overig.e2ehelpers import E2EHelpers
from Mailer.models import MailQueue
from Taken import taken
from .models import Taak
import datetime


class TestTakenTaken(E2EHelpers, TestCase):
    """ unit tests voor de Taken applicatie """

    test_after = ('Functie',)

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = self.e2e_create_account_admin()
        self.account_normaal = self.e2e_create_account('normaal', 'normaal@test.com', 'Normaal')
        self.account_same = self.e2e_create_account('same', 'same@test.com', 'same')

        lid = NhbLid()
        lid.nhb_nr = 100042
        lid.geslacht = "M"
        lid.voornaam = "Beh"
        lid.achternaam = "eerder"
        lid.geboorte_datum = datetime.date(year=1972, month=3, day=4)
        lid.sinds_datum = datetime.date(year=2010, month=11, day=12)
        lid.account = self.account_normaal
        lid.email = lid.account.email
        lid.save()

    def test_aantal_open_taken(self):
        # standaard sessie heeft nog geen opgeslagen aantal taken
        request = self.client
        aantal = taken.aantal_open_taken(request)
        self.assertIsNone(aantal)

    def test_stuur_taak_email_herinnering(self):
        self.assertEqual(0, MailQueue.objects.count())
        email = self.account_normaal.accountemail_set.all()[0]
        taken.stuur_taak_email_herinnering(email, 5)
        self.assertEqual(1, MailQueue.objects.count())

    def test_stuur_nieuwe_taak_email(self):
        self.assertEqual(0, MailQueue.objects.count())
        email = self.account_normaal.accountemail_set.all()[0]
        taken.stuur_nieuwe_taak_email(email, 5)
        self.assertEqual(1, MailQueue.objects.count())

    def test_maak_taak(self):
        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        deadline = datetime.date(2020, 12, 13)

        taken.maak_taak(toegekend_aan=self.account_normaal,
                        deadline=deadline,
                        aangemaakt_door=None,
                        beschrijving="Tekst",
                        handleiding_pagina="Pagina",
                        log="Log")

        self.assertEqual(1, Taak.objects.count())
        self.assertEqual(1, MailQueue.objects.count())

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
        taken.maak_taak(toegekend_aan=self.account_normaal,
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
        taken.maak_taak(toegekend_aan=self.account_normaal,
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
        taken.herinner_aan_taken()
        self.assertEqual(0, MailQueue.objects.count())

    def test_herinner_aan_taken(self):

        deadline = datetime.date(2000, 1, 1)

        self.assertEqual(0, Taak.objects.count())
        self.assertEqual(0, MailQueue.objects.count())

        # maak 3 taken aan voor 2 accounts
        taken.maak_taak(toegekend_aan=self.account_normaal,
                        deadline=deadline,
                        beschrijving="Tekst 1")

        taken.maak_taak(toegekend_aan=self.account_normaal,
                        deadline=deadline,
                        beschrijving="Tekst 2")

        taken.maak_taak(toegekend_aan=self.account_admin,
                        deadline=deadline,
                        beschrijving="Tekst 3")

        self.assertEqual(3, Taak.objects.count())
        self.assertEqual(3, MailQueue.objects.count())

        # vraag nu om herinneringen te sturen
        email = self.account_admin.accountemail_set.all()[0]
        email.laatste_email_over_taken = None
        email.save()

        taken.herinner_aan_taken()
        self.assertEqual(4, MailQueue.objects.count())

        # controleer dat de herinnering pas gestuurd worden na 7 dagen
        email.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) + datetime.timedelta(hours=1)
        email.save()

        taken.herinner_aan_taken()
        self.assertEqual(4, MailQueue.objects.count())

        email.laatste_email_over_taken = timezone.now() - datetime.timedelta(days=7) - datetime.timedelta(hours=1)
        email.save()

        taken.herinner_aan_taken()
        self.assertEqual(5, MailQueue.objects.count())

# end of file
