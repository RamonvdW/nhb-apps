# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase, override_settings
from TestHelpers.e2ehelpers import E2EHelpers


TEST_EMAIL_ADRES = 'schutter@nhb.test'


class TestMailerEmails(E2EHelpers, TestCase):

    """ tests voor de Mailer applicatie """

    test_after = ('Mailer.test_operations', )

    def test_alle_emails(self):
        self.e2e_create_account('123456', TEST_EMAIL_ADRES, 'Test')

        f1, f2 = self.run_management_command('test_alle_emails', TEST_EMAIL_ADRES)
        # print('f1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertFalse("[ERROR]" in f1.getvalue())
        self.assertFalse("[ERROR]" in f2.getvalue())
        self.assertTrue('[WARNING] E-mailadres is niet white-listed' in f2.getvalue())

        f1, f2 = self.run_management_command('test_alle_emails', 'other@hetzalwel')
        self.assertTrue('Geen valide e-mailadres' in f1.getvalue())

        with override_settings(EMAIL_ADDRESS_WHITELIST=()):
            f1, f2 = self.run_management_command('test_alle_emails', 'other@onbeke.nd')
            self.assertTrue('Geen account gevonden met dit e-mailadres' in f1.getvalue())

        with override_settings(EMAIL_ADDRESS_WHITELIST=(TEST_EMAIL_ADRES,)):
            f1, f2 = self.run_management_command('test_alle_emails', TEST_EMAIL_ADRES)
            self.assertTrue('[WARNING] E-mailadres is niet white-listed' not in f2.getvalue())

    def test_status_mail_queue(self):
        f1, f2 = self.run_management_command('status_mail_queue')
        self.assertTrue('MQ:' in f2.getvalue())


# end of file
