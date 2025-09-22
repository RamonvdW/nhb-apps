# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email, mailer_obfuscate_email, mailer_email_is_valide, render_email_template


class TestMailerOperations(TestCase):

    """ tests voor de Mailer applicatie, module Operations """

    def test_queue_mail(self):
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)

        mailer_queue_email('schutter@test.not', 'onderwerp', 'body\ndoei!\n')

        # valideer dat de mail nu in de queue staat
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 1)
        obj = objs[0]

        # validate de velden van de mail
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        self.assertEqual(obj.mail_to, 'schutter@test.not')
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
        self.assertEqual(mailer_obfuscate_email('x@test.not'), 'x@test.not')
        self.assertEqual(mailer_obfuscate_email('do@test.not'), 'd#@test.not')
        self.assertEqual(mailer_obfuscate_email('tre@test.not'), 't#e@test.not')
        self.assertEqual(mailer_obfuscate_email('vier@test.not'), 'v##r@test.not')
        self.assertEqual(mailer_obfuscate_email('zeven@test.not'), 'ze##n@test.not')
        self.assertEqual(mailer_obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_email_is_valide(self):
        self.assertTrue(mailer_email_is_valide('test@test.not'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@test.not'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@hb.nl'))
        self.assertTrue(mailer_email_is_valide('r@hb.nl'))
        self.assertFalse(mailer_email_is_valide('tester@test'))
        self.assertFalse(mailer_email_is_valide('test er@test.not'))
        self.assertFalse(mailer_email_is_valide('test\ter@test.not'))
        self.assertFalse(mailer_email_is_valide('test\ner@test.not'))

    def test_whitelist(self):
        # controleer dat de whitelist zijn werk doet
        self.assertEqual(0, MailQueue.objects.count())

        with override_settings(EMAIL_ADDRESS_WHITELIST=('een.test@test.not',)):
            mailer_queue_email('schutter@test.not', 'onderwerp', 'body\ndoei!\n')
            self.assertEqual(1, MailQueue.objects.count())
            mail = MailQueue.objects.first()
            self.assertTrue(mail.is_blocked)
            mail.delete()

            mailer_queue_email('een.test@test.not', 'onderwerp', 'body\ndoei!\n')
            self.assertEqual(1, MailQueue.objects.count())
            mail = MailQueue.objects.first()
            self.assertFalse(mail.is_blocked)
        # with

    def test_render(self):
        context = {
            'url': 'dit_is_geen_url',
            'naam_site': 'TestSite',
            'contact_email': 'ergens@nerge.ns',
        }
        test_email_template = 'email_account/wachtwoord-vergeten.dtl'

        out_text, out_html, template_used = render_email_template(context, test_email_template)

        self.assertTrue(out_text != '')
        self.assertTrue(out_html != '')
        self.assertEqual(template_used, test_email_template)


# end of file
