# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core import management
from .models import MailQueue, mailer_queue_email, mailer_notify_internal_error, mailer_opschonen
from TestHelpers.e2ehelpers import E2EHelpers
import datetime
import io


# TODO: test van status_mail_queue toevoegen

TEST_EMAIL_ADRES = 'schutter@nhb.test'


class TestMailerCliBase(E2EHelpers, TestCase):

    """ tests voor de Mailer applicatie """

    def test_leeg(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '1', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

    def test_status_mail_queue(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('status_mail_queue', stderr=f1, stdout=f2)
        self.assertTrue('MQ: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

    def test_deliver_faal(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email(TEST_EMAIL_ADRES, 'onderwerp faal', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '1', '--quick', stderr=f1, stdout=f2)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)
        self.assertTrue('[WARNING] ' in f2.getvalue())

    def test_oud(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email(TEST_EMAIL_ADRES, 'onderwerp_1', 'body\ndoei!\n')
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertFalse('(verstuurd)' in str(obj))

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '1', '--quick', stderr=f1, stdout=f2)

        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_nieuw(self):
        # requires websim_mailer.py running in the background
        # om geen multi-threaded test te hoeven maken kunnen we het management commando
        # vragen om geen oude mails te sturen

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email(TEST_EMAIL_ADRES, 'onderwerp_1', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '--skip_old', '--quick', '1', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertFalse('[INFO] Aantal oude mails geprobeerd te versturen:' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_stuur_mail_vertraag(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email(TEST_EMAIL_ADRES, 'onderwerp delay', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20, check_duration=False):
            management.call_command('stuur_mails', '1', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_notify_internal_error(self):
        self.assertEqual(MailQueue.objects.count(), 0)

        tb = "hoi\ndaar"
        mailer_notify_internal_error(tb)
        self.assertEqual(MailQueue.objects.count(), 1)

        # zelfde melding wordt niet nog een keer verstuurd
        mailer_notify_internal_error(tb)
        self.assertEqual(MailQueue.objects.count(), 1)

    def test_opschonen(self):

        # maak een mail aan die lang geleden verstuurd is
        mailer_queue_email('ergens@nergens.niet', 'Test', 'Test', enforce_whitelist=False)
        mail = MailQueue.objects.all()[0]
        mail.toegevoegd_op -= datetime.timedelta(days=92)
        mail.save()

        f1 = io.StringIO()
        mailer_opschonen(f1)
        self.assertTrue('[INFO] Verwijder 1 oude emails' in f1.getvalue())

        f1 = io.StringIO()
        mailer_opschonen(f1)
        self.assertFalse('Verwijder' in f1.getvalue())


class TestMailerCliBadBase(E2EHelpers, TestCase):

    """ tests voor de Mailer applicatie """

    def test_stuur_mails_bad_duration(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(management.base.CommandError):
            management.call_command('stuur_mails', '99999', stderr=f1, stdout=f2)

    def test_stuur_mail_no_connect(self):
        # deze test eist dat de URL wijst naar een poort waar niet op gereageerd wordt
        # zoals http://localhost:9999

        # stop een mail in de queue
        self.assertEqual(MailQueue.objects.count(), 0)
        mailer_queue_email(TEST_EMAIL_ADRES, 'onderwerp', 'body\ndoei!\n')

        self.assertEqual(MailQueue.objects.count(), 1)
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertFalse(obj.is_blocked)
        self.assertEqual(obj.aantal_pogingen, 0)

        # probeer te versturen
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20, check_duration=False):     # duurt 7 seconden
            management.call_command('stuur_mails', '7', '--quick', stderr=f1, stdout=f2)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue('[ERROR] ' in f1.getvalue())


@override_settings(POSTMARK_URL='http://localhost:8123/postmark',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerCliPostmark(TestMailerCliBase):
    pass


# use a port with no service responding to it
@override_settings(POSTMARK_URL='http://localhost:9999',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=(TEST_EMAIL_ADRES,))
class TestMailerCliBadPostmark(TestMailerCliBadBase):
    pass


# voorkomt uitvoeren van de tests in deze base classes
del TestMailerCliBase
del TestMailerCliBadBase


# end of file
