# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core import management
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

#TODO: test models
#TODO: test queue_mail
#TODO: test send_mail

# end of file
