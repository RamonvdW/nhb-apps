# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from Mailer.models import MailQueue
from Mailer.operations import mailer_queue_email
from Mailer.mailer import send_mail


class TestMailerGoodBase(TestCase):

    """ tests voor de Mailer applicatie """

    test_after = ('Mailer.tests.test_operations', )

    def test_send_mail_deliver(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        self.assertEqual(0, MailQueue.objects.count())
        mailer_queue_email('schutter@nhb.test', 'onderwerp', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)

        send_mail(obj)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertTrue(obj.is_verstuurd)

    def test_send_mail_deliver_faal(self):
        # requires websim_mailer.py running in the background

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp faal', ('body\ndoei!\n', '<html>body</html>'))

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)

        send_mail(obj)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)

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


class TestMailerBadBase(TestCase):

    """ tests voor de Mailer applicatie """

    test_after = ('Mailer.tests.test_operations', )

    def test_send_mail_no_connect(self):
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
        send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)

    def test_send_mail_limit(self):
        # deze test eist dat de URL wijst naar een poort waar niet op gereageerd wordt
        # zoals http://localhost:9999

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
        send_mail(obj)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 25)
        old_log = obj.log
        # 25 blijft 25
        send_mail(obj)
        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 25)
        self.assertEqual(obj.log, old_log)


@override_settings(POSTMARK_URL='http://localhost:8123/postmark',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerPostmark(TestMailerGoodBase):
    pass


# use a port with no service responding to it
@override_settings(POSTMARK_URL='http://localhost:9999',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerBadPostmark(TestMailerBadBase):
    pass


# voorkom uitvoeren van tests in de base class
del TestMailerGoodBase
del TestMailerBadBase


# end of file
