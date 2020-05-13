# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
from .models import MailQueue, mailer_queue_email, mailer_obfuscate_email, mailer_email_is_valide
from .mailer import send_mail
import io


class TestMailer(TestCase):
    """ unit tests voor de Mailer applicatie """

    def test_stuur_mails_bad_duration(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(management.base.CommandError):
            management.call_command('stuur_mails', '99999', stderr=f1, stdout=f2)

    def test_stuur_mails(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('stuur_mails', '0', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

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

    def test_no_api_key(self):
        with self.settings(MAILGUN_API_KEY=''):
            send_mail(None)
        # als we hier komen is het goed, want geen exception
        self.assertTrue(True)

    def test_send_mail_no_connect(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        # following port must not have any service responding to it
        with self.settings(MAILGUN_URL='http://localhost:9999'):
            send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)

    def test_stuur_mail_no_connect(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        # following port must not have any service responding to it
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.settings(MAILGUN_URL='http://localhost:9999'):
            management.call_command('stuur_mails', '0', stderr=f1, stdout=f2)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue('[ERROR] ' in f1.getvalue())

    def test_send_mail_deliver(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        # following requires websim.py running in the background
        with self.settings(MAILGUN_URL='http://localhost:8123/v3/testdomain1.com/messages',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue(obj.is_verstuurd)

    def test_send_mail_deliver_faal(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp faal', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        # following requires websim.py running in the background
        with self.settings(MAILGUN_URL='http://localhost:8123/v3/testdomain2.com/messages',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)

    def test_stuur_mail_deliver_faal(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp faal', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        f1 = io.StringIO()
        f2 = io.StringIO()
        # following requires websim.py running in the background
        with self.settings(MAILGUN_URL='http://localhost:8123/v3/testdomain2.com/messages',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            management.call_command('stuur_mails', '0', stderr=f1, stdout=f2)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)
        self.assertTrue('[WARNING] ' in f2.getvalue())

    def test_send_mail_limit(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # controleer dat we ophouden te proberen na 25 pogingen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)
        # 24 naar 25
        obj.aantal_pogingen = 24
        obj.save()
        # following port must not have any service responding to it
        with self.settings(MAILGUN_URL='http://localhost:9999',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 25)
        old_log = obj.log
        # 25 blijft 25
        # following port must not have any service responding to it
        with self.settings(MAILGUN_URL='http://localhost:9999',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 25)
        self.assertEqual(obj.log, old_log)

    def test_stuur_mail_1(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp_1', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.settings(MAILGUN_URL='http://localhost:8123/v3/testdomain3.com/messages',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            management.call_command('stuur_mails', '0', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_stuur_mail_vertraag(self):
        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp delay', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.settings(MAILGUN_URL='http://localhost:8123/v3/testdomain3.com/messages',
                           MAILGUN_API_KEY='the-api-key',
                           EMAIL_FROM_ADDRESS='noreply@nhb.test'):
            management.call_command('stuur_mails', '0', stderr=f1, stdout=f2)
        #print("f1: %s" % f1.getvalue())
        #print("f2: %s" % f2.getvalue())
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

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

# end of file
