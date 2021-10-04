# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings


class TestBondspas(object):

    """ tests voor de Bondspas applicatie """

    def test_queue_mail(self):
        assert isinstance(self, TestCase)

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

    def test_send_mail_deliver(self):
        # requires websim_mailer.py running in the background
        assert isinstance(self, TestCase)

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
        assert isinstance(self, TestCase)

        # stop een mail in de queue
        objs = MailQueue.objects.all()
        self.assertEqual(len(objs), 0)
        mailer_queue_email('schutter@nhb.test', 'onderwerp faal', 'body\ndoei!\n')

        # probeer te versturen
        obj = MailQueue.objects.all()[0]
        self.assertFalse(obj.is_verstuurd)
        self.assertEqual(obj.aantal_pogingen, 0)

        send_mail(obj)

        obj = MailQueue.objects.all()[0]
        self.assertEqual(obj.aantal_pogingen, 1)
        self.assertFalse(obj.is_verstuurd)

    def test_obfuscate_email(self):
        assert isinstance(self, TestCase)
        self.assertEqual(mailer_obfuscate_email(''), '')
        self.assertEqual(mailer_obfuscate_email('x'), 'x')
        self.assertEqual(mailer_obfuscate_email('x@test.nhb'), 'x@test.nhb')
        self.assertEqual(mailer_obfuscate_email('do@test.nhb'), 'd#@test.nhb')
        self.assertEqual(mailer_obfuscate_email('tre@test.nhb'), 't#e@test.nhb')
        self.assertEqual(mailer_obfuscate_email('vier@test.nhb'), 'v##r@test.nhb')
        self.assertEqual(mailer_obfuscate_email('zeven@test.nhb'), 'ze##n@test.nhb')
        self.assertEqual(mailer_obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_email_is_valide(self):
        assert isinstance(self, TestCase)
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
        assert isinstance(self, TestCase)

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


class TestMailerBadBase(object):
    """ tests voor de Mailer applicatie """

    def test_no_api_key(self):
        assert isinstance(self, TestCase)
        with self.settings(POSTMARK_API_KEY=''):
            send_mail(None)

        # als we hier komen is het goed, want geen exception
        self.assertTrue(True)

    def test_send_mail_no_connect(self):
        # deze test eist dat de URL wijst naar een poort waar niet op gereageerd wordt
        # zoals http://localhost:9999
        assert isinstance(self, TestCase)

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
        assert isinstance(self, TestCase)

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

    def test_obfuscate_email(self):
        assert isinstance(self, TestCase)
        self.assertEqual(mailer_obfuscate_email(''), '')
        self.assertEqual(mailer_obfuscate_email('x'), 'x')
        self.assertEqual(mailer_obfuscate_email('x@test.nhb'), 'x@test.nhb')
        self.assertEqual(mailer_obfuscate_email('do@test.nhb'), 'd#@test.nhb')
        self.assertEqual(mailer_obfuscate_email('tre@test.nhb'), 't#e@test.nhb')
        self.assertEqual(mailer_obfuscate_email('vier@test.nhb'), 'v##r@test.nhb')
        self.assertEqual(mailer_obfuscate_email('zeven@test.nhb'), 'ze##n@test.nhb')
        self.assertEqual(mailer_obfuscate_email('hele.lange@maaktnietuit.nl'), 'he#######e@maaktnietuit.nl')

    def test_email_is_valide(self):
        assert isinstance(self, TestCase)
        self.assertTrue(mailer_email_is_valide('test@nhb.nl'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@nhb.nl'))
        self.assertTrue(mailer_email_is_valide('jan.de.tester@hb.nl'))
        self.assertTrue(mailer_email_is_valide('r@hb.nl'))
        self.assertFalse(mailer_email_is_valide('tester@nhb'))
        self.assertFalse(mailer_email_is_valide('test er@nhb.nl'))
        self.assertFalse(mailer_email_is_valide('test\ter@nhb.nl'))
        self.assertFalse(mailer_email_is_valide('test\ner@nhb.nl'))


@override_settings(POSTMARK_URL='http://localhost:8123/postmark',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerPostmark(TestMailerBase, TestCase):
    pass


# use a port with no service responding to it
@override_settings(POSTMARK_URL='http://localhost:9999',
                   POSTMARK_API_KEY='the-api-key',
                   EMAIL_FROM_ADDRESS='noreply@nhb.test',
                   EMAIL_ADDRESS_WHITELIST=())
class TestMailerBadPostmark(TestMailerBadBase, TestCase):
    pass


# end of file
