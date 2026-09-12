# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from GraphDrive.operations.access_token import get_bearer_token
from GraphDrive.operations import GraphSite
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
from requests.exceptions import SSLError
from datetime import timedelta
import io


class ResponseMock:

    def __init__(self, status_code=200, token_type='Bearer', complete=True):
        self.status_code = status_code
        self.text = 'mock'
        self.encoding = 'mock'
        self._token_type = token_type
        self._complete = complete

    def json(self):
        d = {
            'token_type': self._token_type,
            'access_token': 'test token',
        }
        if self._complete:
            d['expires_in'] = 60

        return d


class TestGraphDriveOpAccessToken(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module access_token """

    def test_bearer(self):
        out = OutputWrapper(io.StringIO())
        site = GraphSite(out)
        self.token_url_template = 'http://localhost:55555/%s/'      # avoid going to real site

        # connection error

        out = OutputWrapper(io.StringIO())
        with patch('requests.post', side_effect=SSLError('uitzondering')):
            res = get_bearer_token(out, site)
            self.assertFalse(res)
        self.assertTrue('[ERROR] Exceptie bij versturen access token request: uitzondering' in out.getvalue())

        # foutcode
        resp = ResponseMock(status_code=404)
        out = OutputWrapper(io.StringIO())
        with patch('requests.post', return_value=resp):
            res = get_bearer_token(out, site)
            self.assertFalse(res)
        self.assertTrue("[ERROR] Access token request gaf onverwacht antwoord! response encoding:'mock', status_code:404" in out.getvalue())

        # verkeerd type
        resp = ResponseMock(token_type='Verkeerd')
        out = OutputWrapper(io.StringIO())
        with patch('requests.post', return_value=resp):
            res = get_bearer_token(out, site)
            self.assertFalse(res)
        # print('out:', out.getvalue())
        self.assertTrue("[ERROR] Not a bearer access token " in out.getvalue())

        # velden ontbreken
        resp = ResponseMock(complete=False)
        out = OutputWrapper(io.StringIO())
        with patch('requests.post', return_value=resp):
            res = get_bearer_token(out, site)
            self.assertFalse(res)
        # print('out:', out.getvalue())
        self.assertTrue("[ERROR] Not a complete bearer access token" in out.getvalue())

        # goed antwoord
        resp = ResponseMock()
        out = OutputWrapper(io.StringIO())
        with patch('requests.post', return_value=resp):
            res = get_bearer_token(out, site)
            self.assertTrue(res)
            self.assertEqual(site.bearer_token, 'test token')
        # print('out:', out.getvalue())

        # check caching
        site.bearer_token = 'nog een test'
        site.bearer_valid_until = timezone.now() + timedelta(seconds=60)
        out = OutputWrapper(io.StringIO())
        res = get_bearer_token(out, site)
        # print('out:', out.getvalue())
        self.assertTrue(res)
        self.assertEqual(site.bearer_token, 'nog een test')     # niet ververst


# end of file
