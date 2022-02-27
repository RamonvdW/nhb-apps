# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Mailer.models import MailQueue
from NhbStructuur.models import NhbRegio
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestPleinFout(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    url_speciale_pagina = '/plein/test-speciale-pagina/%s/'     # code

    @classmethod
    def setUpTestData(cls):
        cls.testdata = testdata.TestData()
        cls.testdata.maak_accounts()

    def test_403(self):
        # niet ingelogd
        resp = self.client.get(self.url_speciale_pagina % '403a')
        self.assert_is_redirect(resp, '/account/login/')

        self.e2e_login(self.testdata.account_admin)

        resp = self.client.get(self.url_speciale_pagina % '403a')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_speciale_pagina % '403b')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

    def test_404(self):
        resp = self.client.get(self.url_speciale_pagina % '404a')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_speciale_pagina % '404b')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_speciale_pagina % '404c')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        resp = self.client.get(self.url_speciale_pagina % '42')
        self.assertTrue(resp.status_code, 200)
        self.assertContains(resp, 'Niet ondersteunde code')
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        resp = self.client.get('/plein/seems-part-of-site/')
        self.assertTrue(resp.status_code, 200)

        resp = self.client.get('/searching-for-weakness/something/')
        self.assertTrue(resp.status_code, 404)

        resp = self.client.get('/some-icon.png')
        self.assertTrue(resp.status_code, 404)

    def test_500(self):
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertTrue(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_500.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)
        self.assertEqual(1, MailQueue.objects.count())

        # nog een keer, zodat de email naar de ontwikkelaar er al is
        # controleer dat er maar 1 mail geschreven wordt (per dag)
        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertTrue(resp.status_code, 200)
        self.assertEqual(1, MailQueue.objects.count())

        # nu met een actieve functie

        func = Functie(
                    beschrijving="Test Functie 1234",
                    rol='RCL',
                    nhb_regio=NhbRegio.objects.get(regio_nr=104))
        func.save()
        func.accounts.add(self.testdata.account_bb)

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(func)
        self.e2e_check_rol('RCL')

        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertTrue(resp.status_code, 200)
        self.assertEqual(2, MailQueue.objects.count())

# end of file
