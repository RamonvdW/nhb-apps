# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Account.operations.aanmaken import account_create
from Feedback.models import Feedback
from Feedback.operations import store_feedback
from Logboek.models import LogboekRegel, schrijf_in_logboek
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email
from Registreer.definities import REGISTRATIE_FASE_CLUB, REGISTRATIE_FASE_CONFIRM, REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TijdelijkeCodes.models import save_tijdelijke_code
import datetime


class TestPleinCliDatabaseOpschonen(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie, management command database_opschonen """

    maxDiff = None
    gast_email_een = 'een@gasten.net'
    gast_email_twee = 'twee@gasten.net'
    gast_email_vier = 'vier@gasten.net'

    def setUp(self):
        """ initialisatie van de test case """

        # maak een onvoltooid account aan
        account = account_create(
                        'test',
                        'Voornaam',
                        'Achternaam',
                        'maak niet echt uit',      # password
                        'testje@achternaam.nl',
                        email_is_bevestigd=False)
        account.date_joined -= datetime.timedelta(days=4)
        account.save()

        # maak een oude logboek regel aan
        schrijf_in_logboek(None, 'Test', 'Just testing')
        regel = LogboekRegel.objects.get(gebruikte_functie='Test')
        regel.toegevoegd_op -= datetime.timedelta(days=549)
        regel.save()

        # maak een mail aan die lang geleden verstuurd is
        mailer_queue_email('ergens@nergens.niet', 'Test', 'Test', enforce_whitelist=False)
        mail = MailQueue.objects.first()
        mail.toegevoegd_op -= datetime.timedelta(days=92)
        mail.save()

        # maak een tijdelijke code aan
        save_tijdelijke_code('code', 'test', geldig_dagen=-8)

        # maak een oude, afgehandelde site feedback aan
        store_feedback('mij', 'rol', 'pagina', '/pagina/', Feedback.url2bev['plus'], 'feedback')
        feedback = Feedback.objects.first()
        feedback.toegevoegd_op -= datetime.timedelta(days=92)
        feedback.is_afgehandeld = True
        feedback.save()

        # maak een afgehandelde taak aan
        Taak(is_afgerond=True,
             deadline='2020-01-01',
             beschrijving='test').save()

        long_ago = timezone.now() - datetime.timedelta(days=10)
        gast = GastRegistratie(lid_nr=800001,
                               email_is_bevestigd=True, email=self.gast_email_een)
        gast.save()
        gast.aangemaakt = long_ago
        gast.save(update_fields=['aangemaakt'])

        # maak een onvoltooid account aan
        account = account_create(
                        '800002',
                        'Tweede',
                        'Gast',
                        'maakt niet echt uit',      # password
                        self.gast_email_twee,
                        email_is_bevestigd=True)
        account.date_joined -= datetime.timedelta(days=4)
        account.save()

        gast = GastRegistratie(lid_nr=800002,
                               email_is_bevestigd=True, email=self.gast_email_twee,
                               fase=REGISTRATIE_FASE_CLUB,
                               account=account)
        gast.save()
        gast.aangemaakt = long_ago
        gast.save(update_fields=['aangemaakt'])

        gast = GastRegistratie(lid_nr=800003, email_is_bevestigd=False)
        gast.save()
        gast.aangemaakt = long_ago
        gast.save(update_fields=['aangemaakt'])

        # maak een onvoltooid account aan
        account = account_create(
                        '800004',
                        'Vierde',
                        'Gast',
                        'maakt niet echt uit',      # password
                        self.gast_email_vier,
                        email_is_bevestigd=True)
        account.date_joined -= datetime.timedelta(days=4)
        account.save()

        sporter = Sporter(
                        lid_nr=800004,
                        geboorte_datum='2000-01-01',
                        sinds_datum='2023-07-01',
                        account=account)
        sporter.save()

        gast = GastRegistratie(lid_nr=800004, fase=REGISTRATIE_FASE_CONFIRM,
                               email_is_bevestigd=True, email=self.gast_email_vier,
                               account=account, sporter=sporter)
        gast.save()
        gast.aangemaakt = long_ago
        gast.save(update_fields=['aangemaakt'])

        # complete registraties mogen niet automatisch verwijderd worden
        gast = GastRegistratie(lid_nr=800005, fase=REGISTRATIE_FASE_COMPLEET)
        gast.save()
        gast.aangemaakt = long_ago
        gast.save(update_fields=['aangemaakt'])

    def test_alles(self):
        with self.assert_max_queries(130, modify_acceptable=True):
            f1, f2 = self.run_management_command('database_opschonen')
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Klaar" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder onvoltooid account Voornaam Achternaam (test)" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder 1 oude logboek regels" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder 1 oude emails" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder ongebruikte tijdelijke url" in f2.getvalue())
        self.assertTrue('[INFO] Verwijder 1 afgehandelde feedback' in f2.getvalue())
        self.assertTrue('[INFO] Verwijder niet afgeronde gast-account registratie 800001 in fase 0' in f2.getvalue())

        # nog een keer aanroepen terwijl er niets meer te verwijderen valt
        with self.assert_max_queries(10):
            f1, f2 = self.run_management_command('database_opschonen')
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Klaar" in f2.getvalue())
        # self.assertFalse("[INFO]" in f2.getvalue())

        self.assertEqual(GastRegistratie.objects.count(), 1)

        self.assertEqual(3, MailQueue.objects.count())
        for mail in MailQueue.objects.all():
            self.assertIn(mail.mail_to, (self.gast_email_een, self.gast_email_twee, self.gast_email_vier))
            self.assert_email_html_ok(mail)
            self.assert_consistent_email_html_text(mail)
        # for

# end of file
