# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from Account.operations.aanmaken import account_create
from Feedback.models import Feedback
from Feedback.operations import store_feedback
from Logboek.models import LogboekRegel, schrijf_in_logboek
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email
from Taken.models import Taak
from TestHelpers.e2ehelpers import E2EHelpers
from TijdelijkeCodes.models import save_tijdelijke_code
import datetime
import io


class TestPleinCliDatabaseOpschonen(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie, management command database_opschonen """

    maxDiff = None
    
    def setUp(self):
        """ initialisatie van de test case """

        # maak een onvoltooid account aan
        account = account_create(
                        'test',
                        'Voornaam',
                        'Achternaam',
                        'fdsli131982c$114',      # password
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
        mail = MailQueue.objects.all()[0]
        mail.toegevoegd_op -= datetime.timedelta(days=92)
        mail.save()

        # maak een tijdelijke code aan
        save_tijdelijke_code('code', 'test', geldig_dagen=-8)

        # maak een oude, afgehandelde site feedback aan
        store_feedback('mij', 'rol', 'pagina', '/pagina/', Feedback.url2bev['plus'], 'feedback')
        feedback = Feedback.objects.all()[0]
        feedback.toegevoegd_op -= datetime.timedelta(days=92)
        feedback.is_afgehandeld = True
        feedback.save()

        # maak een afgehandelde taak aan
        Taak(is_afgerond=True,
             deadline='2020-01-01',
             beschrijving='test').save()

    def test_alles(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(34):
            management.call_command('database_opschonen', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Klaar" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder onvoltooid account Voornaam Achternaam (test)" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder 1 oude logboek regels" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder 1 oude emails" in f2.getvalue())
        self.assertTrue("[INFO] Verwijder ongebruikte tijdelijke url" in f2.getvalue())
        self.assertTrue('[INFO] Verwijder 1 afgehandelde feedback' in f2.getvalue())

        # nog een keer aanroepen terwijl er niets meer te verwijderen valt
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(10):
            management.call_command('database_opschonen', stderr=f1, stdout=f2)
        self.assertTrue(f1.getvalue() == '')
        self.assertTrue("Klaar" in f2.getvalue())
        self.assertFalse("[INFO]" in f2.getvalue())


# end of file
