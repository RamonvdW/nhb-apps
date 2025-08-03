# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Functie.models import Functie
from Functie.tests.helpers import maak_functie
from Geo.models import Regio
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers import testdata


class TestPleinFout(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    url_speciale_pagina = '/plein/test-speciale-pagina/%s/'     # code

    @classmethod
    def setUpTestData(cls):
        cls.testdata = data = testdata.TestData()
        data.maak_accounts_admin_en_bb()

    def test_403(self):
        # niet ingelogd
        resp = self.client.get(self.url_speciale_pagina % '403a')
        self.assert_is_redirect(resp, '/account/login/')

        # redirect naar login pagina met "next" parameter
        resp = self.client.get('/bondspas/toon/')
        self.assert_is_redirect(resp, '/account/login/?next=/bondspas/toon/')

        resp = self.client.get('/sporter/')
        self.assert_is_redirect(resp, '/account/login/?next=/sporter/')

        resp = self.client.get('/scheidsrechter/')
        self.assert_is_redirect(resp, '/account/login/?next=/scheidsrechter/')

        # log in
        self.testdata.account_admin.is_BB = True
        self.testdata.account_admin.save()
        self.e2e_account_accepteert_vhpg(self.testdata.account_admin)
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        resp = self.client.get(self.url_speciale_pagina % '403a')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="sporter"')

        resp = self.client.get(self.url_speciale_pagina % '403b')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_403.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

        # rol
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        resp = self.client.get('/wedstrijden/manager/')     # accepteert alleen MWZ
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="BB"')

        functie = maak_functie('RCL 111', 'RCL')
        functie.accounts.add(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(functie)
        resp = self.client.get('/wedstrijden/manager/')     # accepteert alleen MWZ
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="RCL"')
        self.assertContains(resp, 'property="mh:functie"')
        self.assertContains(resp, 'content="RCL 111"')

    def test_404(self):
        # niet ingelogd
        resp = self.client.get(self.url_speciale_pagina % '404a')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="geen"')
        self.assertNotContains(resp, 'property="mh:functie"')

        resp = self.client.get(self.url_speciale_pagina % '404b')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)

        resp = self.client.get(self.url_speciale_pagina % '404c')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        resp = self.client.get(self.url_speciale_pagina % '42')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Niet ondersteunde code')
        self.assert_template_used(resp, ('plein/fout_404.dtl', 'plein/site_layout_minimaal.dtl'))

        resp = self.client.get('/plein/seems-part-of-site/')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get('/searching-for-weakness/something/')
        self.assertEqual(resp.status_code, 404)

        resp = self.client.get('/some-icon.png')
        self.assertEqual(resp.status_code, 404)

        # log in
        self.testdata.account_admin.is_BB = True
        self.testdata.account_admin.save()
        self.e2e_account_accepteert_vhpg(self.testdata.account_admin)
        self.e2e_login_and_pass_otp(self.testdata.account_admin)

        resp = self.client.get(self.url_speciale_pagina % '404a')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="sporter"')
        self.assertNotContains(resp, 'property="mh:functie"')

        # rol
        self.e2e_wisselnaarrol_bb()
        self.e2e_check_rol('BB')
        resp = self.client.get(self.url_speciale_pagina % '404a')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="BB"')
        self.assertNotContains(resp, 'property="mh:functie"')

        functie = maak_functie('RCL 111', 'RCL')
        functie.accounts.add(self.testdata.account_admin)
        self.e2e_wissel_naar_functie(functie)
        resp = self.client.get(self.url_speciale_pagina % '404a')
        self.assertContains(resp, 'property="mh:rol"')
        self.assertContains(resp, 'content="RCL"')
        self.assertContains(resp, 'property="mh:functie"')
        self.assertContains(resp, 'content="RCL 111"')


    def test_500(self):
        self.assertEqual(0, MailQueue.objects.count())
        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertEqual(resp.status_code, 200)
        self.assert_template_used(resp, ('plein/fout_500.dtl', 'plein/site_layout_minimaal.dtl'))
        self.assert_html_ok(resp)
        self.assertEqual(1, MailQueue.objects.count())

        # nog een keer, zodat de email naar de ontwikkelaar er al is.
        # controleer dat er maar 1 mail geschreven wordt (per dag)
        with self.assert_max_queries(20):                               # provides code 500 support in query tracer
            resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(1, MailQueue.objects.count())

        # nu met een actieve functie

        func = Functie(
                    beschrijving="Test Functie 1234",
                    rol='RCL',
                    regio=Regio.objects.get(regio_nr=104))
        func.save()
        func.accounts.add(self.testdata.account_bb)

        self.e2e_login_and_pass_otp(self.testdata.account_bb)
        self.e2e_wissel_naar_functie(func)
        self.e2e_check_rol('RCL')

        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(2, MailQueue.objects.count())

    def test_append_slash(self):
        # cooperation between view_fout and CommonMiddleware

        # --> plein/ via middleware
        resp = self.client.get('/plein')
        self.assert_is_permanent_redirect(resp, '/plein/')

        resp = self.client.get('/plein?test=1')
        self.assert_is_permanent_redirect(resp, '/plein/?test=1')


# end of file
