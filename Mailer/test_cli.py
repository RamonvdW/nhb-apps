# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from django.core import management
from .models import MailQueue, mailer_queue_email
from Overig.e2ehelpers import E2EHelpers
import io


class TestMailerCliBase(E2EHelpers, object):
    """ unit tests voor de Mailer applicatie """

    def test_leeg(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

    def test_deliver_faal(self):
        # requires websim.py running in the background

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
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '2', '--quick', stderr=f1, stdout=f2)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)
        self.assertTrue('[WARNING] ' in f2.getvalue())

    def test_oud(self):
        # requires websim.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp_1', 'body\ndoei!\n')
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertFalse('(verstuurd)' in str(obj))

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '2', '--quick', stderr=f1, stdout=f2)

        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_nieuw(self):
        # requires websim.py running in the background
        # om geen multi-threaded test te hoeven maken kunnen we het management commando
        # vragen om geen oude mails te sturen

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp_1', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '--skip_old', '--quick', '2', stderr=f1, stdout=f2)
        # print("f1: %s" % f1.getvalue())
        # print("f2: %s" % f2.getvalue())

        self.assertFalse('[INFO] Aantal oude mails geprobeerd te versturen:' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))

    def test_stuur_mail_vertraag(self):
        # requires websim.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp delay', 'body\ndoei!\n')

        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '2', '--quick', stderr=f1, stdout=f2)
        self.assertTrue('[INFO] Aantal oude mails geprobeerd te versturen: 1' in f2.getvalue())
        self.assertTrue('[INFO] Aantal nieuwe mails geprobeerd te versturen: 0' in f2.getvalue())
        self.assertEqual(f1.getvalue(), '')

        obj = MailQueue.objects.all()[0]
        self.assertTrue(obj.is_verstuurd)
        self.assertTrue('(verstuurd)' in str(obj))


class TestMailerCliBadBase(E2EHelpers, object):
    """ unit tests voor de Mailer applicatie """

    def test_stuur_mails_bad_duration(self):
        f1 = io.StringIO()
        f2 = io.StringIO()
        with self.assertRaises(management.base.CommandError):
            management.call_command('stuur_mails', '99999', stderr=f1, stdout=f2)

    def test_stuur_mail_no_connect(self):
        # deze test eist dat de URL wijst naar een poort waar niet op gereageerd wordt
        # zoals http://localhost:9999

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
        with self.assert_max_queries(20):
            management.call_command('stuur_mails', '7', '--quick', stderr=f1, stdout=f2)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue('[ERROR] ' in f1.getvalue())


@override_settings(POSTMARK_URL='http://localhost:8123/postmark',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerCliPostmark(TestMailerCliBase, TestCase):
    pass


# use a port with no service responding to it
@override_settings(POSTMARK_URL='http://localhost:9999',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerCliBadPostmark(TestMailerCliBadBase, TestCase):
    pass


# end of file
