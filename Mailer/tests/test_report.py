# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Account.models import Account
from Functie.models import Functie
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email
from Mailer.mailer import send_mail
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from Taken.models import Taak


class TestMailerGoodBase(TestCase):

    """ tests voor de Mailer applicatie """

    test_after = ('Mailer.tests.test_operations', )

    bad_email = 'user@bounce.now'

    def setUp(self):
        Account(
            username='account1',
            bevestigde_email=self.bad_email,
            nieuwe_email=self.bad_email).save()

        Functie(
            rol='RCL',
            bevestigde_email=self.bad_email,
            nieuwe_email=self.bad_email).save()

        GastRegistratie(
            email=self.bad_email).save()

        Sporter(
            lid_nr=123456,
            geboorte_datum='1999-09-09',
            sinds_datum='2022-02-02',
            email=self.bad_email).save()

    def test_bounce(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        self.assertEqual(0, MailQueue.objects.count())
        mailer_queue_email(self.bad_email, 'onderwerp', 'body\ndoei!\n')

        self.assertEqual(0, Taak.objects.count())

        # probeer te versturen
        obj = MailQueue.objects.first()
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)

        send_mail(obj)

        obj = MailQueue.objects.first()
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue(obj.is_blocked)
        self.assertFalse(obj.is_verstuurd)

        self.assertEqual(1, Taak.objects.count())

        # check dat we geen dubbele taak aanmaken
        send_mail(obj)
        self.assertEqual(1, Taak.objects.count())


@override_settings(POSTMARK_URL='http://localhost:8123/postmark',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@test.not',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerPostmark(TestMailerGoodBase):
    pass


# voorkom uitvoeren van tests in de base class
del TestMailerGoodBase


# end of file
