# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email, mailer_obfuscate_email, mailer_email_is_valide


class TestMailerOperations(TestCase):

    """ tests voor de Mailer applicatie, module Operations """

    def test_queue_mail(self):
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)

        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # valideer dat de mail nu in de queue staat
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 1)
        obj = objs[0]

        # validate de velden van de mail
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        self.assertEqual(obj.mail_to, 'schutter@nhb.test')
        self.assertEqual(obj.mail_subj, 'onderwerp')
        self.assertEqual(obj.mail_text, 'body\ndoei!\n')
        self.assertTrue("onderwerp" in str(obj))

        # controleer dat een leeg to-adres niet in de queue beland
        self.assertEqual(1, MailQueue.objects.count())
        mailer_queue_email('', 'onderwerp', 'body\ndoei!\n')
        self.assertEqual(1, MailQueue.objects.count())

    def test_obfuscate_email(self):
        self.assertEqual(mailer_obfuscate_email(''), '')
        self.assertEqual(mailer_obfuscate_email('x'), 'x')
        self.assertEqual(mailer_obfuscate_email('x@test.nhb'), 'x@test.nhb')
        self.assertEqual(mailer_obfuscate_email('do@test.nhb'), 'd#@test.nhb')
        self.assertEqual(mailer_obfuscate_email('tre@test.nhb'), 't#e@test.nhb')
        self.assertEqual(mailer_obfuscate_email('vier@test.nhb'), 'v##r@test.nhb')
        self.assertEqual(mailer_obfuscate_email('zeven@test.nhb'), 'ze##n@test.nhb')
        self.assertEqual(mailer_obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_email_is_valide(self):
        self.assertTrue(mailer_email_is_valide('test@nhb.nl'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@nhb.nl'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@hb.nl'))
        self.assertTrue(mailer_email_is_valide('r@hb.nl'))
        self.assertFalse(mailer_email_is_valide('tester@nhb'))
        self.assertFalse(mailer_email_is_valide('test er@nhb.nl'))
        self.assertFalse(mailer_email_is_valide('test\ter@nhb.nl'))
        self.assertFalse(mailer_email_is_valide('test\ner@nhb.nl'))

    def test_whitelist(self):
        # controleer dat de whitelist zijn werk doet
        self.assertEqual(0, MailQueue.objects.count())

        with self.settings(EMAIL_ADDRESS_WHITELIST=('een.test@nhb.not',)):
            mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')
            self.assertEqual(1, MailQueue.objects.count())
            mail = MailQueue.objects.all()[0]
            self.assertTrue(mail.is_blocked)
            mail.delete()

            mailer_queue_email('een.test@nhb.not', 'onderwerp', 'body\ndoei!\n')
            self.assertEqual(1, MailQueue.objects.count())
            mail = MailQueue.objects.all()[0]
            self.assertFalse(mail.is_blocked)
        # with


# end of file
