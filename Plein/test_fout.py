# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Mailer.models import MailQueue
from TestHelpers.e2ehelpers import E2EHelpers


class TestPleinFout(E2EHelpers, TestCase):

    """ tests voor de Plein applicatie """

    url_speciale_pagina = '/plein/test-speciale-pagina/%s/'     # code

    def test_403(self):
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
        resp = self.client.get(self.url_speciale_pagina % '500')
        self.assertTrue(resp.status_code, 200)

        # controleer dat er maar 1 mail geschreven wordt (per dag)
        self.assertEqual(1, MailQueue.objects.count())

# end of file
