# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from GraphDrive.operations import GraphSite
from GraphDrive.operations.last_modified import get_file_metadata, get_file_last_modified
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from requests.exceptions import SSLError
from unittest.mock import patch
from types import SimpleNamespace


class ResponseMock:

    def __init__(self):
        self.status_code = 200
        self.text = 'mock'
        self.encoding = 'mock'
        self._has_value = True

    @staticmethod
    def json():
        return {
            'lastModifiedDateTime': '2026-04-05T19:10:08Z'
        }


class TestGraphDriveOpLastModified(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module last_modified """

    resp_status_400 = SimpleNamespace(status_code=400, encoding='utf-8', text='test1')
    resp_status_200 = ResponseMock()

    def setUp(self):
        self.mock_get_bearer_token_true = patch('GraphDrive.operations.last_modified.get_bearer_token',
                                                return_value=True)
        self.mock_get_bearer_token_false = patch('GraphDrive.operations.last_modified.get_bearer_token',
                                                 return_value=False)

        self.mock_get_drive_id_false = patch('GraphDrive.operations.last_modified.get_drive_id',
                                             return_value=False)
        self.mock_get_drive_id_true = patch('GraphDrive.operations.last_modified.get_drive_id',
                                            return_value=True)

        self.mock_requests_get_status_400 = patch('GraphDrive.operations.last_modified.requests.get',
                                                  return_value=self.resp_status_400)
        self.mock_requests_get_status_200 = patch('GraphDrive.operations.last_modified.requests.get',
                                                  return_value=self.resp_status_200)

        self.mock_get_file_metadata_nok = patch('GraphDrive.operations.last_modified.get_file_metadata',
                                                return_value=None)
        self.mock_get_file_metadata_ok = patch('GraphDrive.operations.last_modified.get_file_metadata',
                                               return_value={'lastModifiedDateTime': '2022-01-01T00:00:00Z'})

    def test_get_file_metadata(self):
        fname = '/remote/doesnotexist.txt'
        self.token_url_template = 'http://localhost:55555/%s/'      # avoid going to real site

        # get_bearer_token fails
        out = OutputBuffer()
        site = GraphSite(out)
        self.mock_get_bearer_token_false.start()
        res = get_file_metadata(out, site, fname)
        self.assertFalse(res)
        self.mock_get_bearer_token_false.stop()
        self.mock_get_bearer_token_true.start()

        # get_drive_id fails
        out = OutputBuffer()
        site = GraphSite(out)
        res = get_file_metadata(out, site, fname)
        self.mock_get_drive_id_false.start()
        self.assertIsNone(res)
        self.mock_get_drive_id_false.stop()
        self.mock_get_drive_id_true.start()

        out = OutputBuffer()
        site = GraphSite(out)
        self.mock_requests_get_status_400.start()
        res = get_file_metadata(out, site, fname)
        self.assertIsNone(res)
        self.assertTrue('[ERROR] {get_file_metadata} request gaf onverwacht antwoord' in out.getvalue())
        self.mock_requests_get_status_400.stop()

        # connection error
        out = OutputBuffer()
        site = GraphSite(out)
        with patch('requests.get', side_effect=SSLError('uitzondering')):
            res = get_file_metadata(out, site, fname)
            self.assertIsNone(res)
        self.assertTrue('[ERROR] {get_file_metadata} Exceptie tijdens request: uitzondering' in out.getvalue())

        out = OutputBuffer()
        site = GraphSite(out)
        self.mock_requests_get_status_200.start()
        res = get_file_metadata(out, site, fname)
        assert isinstance(res, dict)
        self.assertTrue('lastModifiedDateTime' in res.keys())
        self.mock_requests_get_status_200.stop()

        self.mock_get_drive_id_true.stop()
        self.mock_get_bearer_token_true.stop()

    def test_get_file_last_modified(self):
        fpath = '/whatever.txt'

        out = OutputBuffer()
        site = GraphSite(out)
        self.mock_get_file_metadata_nok.start()
        res = get_file_last_modified(out, site, fpath)
        self.assertEqual(res, '')
        self.mock_get_file_metadata_nok.stop()

        self.mock_get_file_metadata_ok.start()
        res = get_file_last_modified(out, site, fpath)
        self.assertEqual(res, '2022-01-01T00:00:00Z')
        self.mock_get_file_metadata_ok.stop()


# end of file
