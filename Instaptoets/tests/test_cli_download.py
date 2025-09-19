# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from TestHelpers.e2ehelpers import E2EHelpers
from googleapiclient.errors import HttpError
from google.auth.exceptions import TransportError
from unittest.mock import patch
from httplib2 import Response
import socket
import tempfile
import os.path
import json


class HttpMock:

    def __init__(self, verbose=False):
        self._verbose = verbose
        self._next_error = None

    def prime_error(self, error_str: str, match: str, error_type: str):
        self._next_error = (error_str, match, error_type)

    def close(self):
        pass

    @staticmethod
    def _mock_oauth():
        json_data = {
            "access_token": "1234",
        }
        return json_data

    @staticmethod
    def _mock_list_sheets():
        sheet1 = {
            "properties": {
                "title": "Sheet1",
            }
        }

        json_data = {
            "sheets": [sheet1],
        }
        return json_data

    @staticmethod
    def _query_params_to_dict(query_str):
        # a=1&b=2
        d = dict()
        for one in query_str.split('&'):
            # a=1
            if "=" in one:      # pragma: no branch
                param, value = one.split('=')
            else:               # pragma: no cover
                param, value = one, ''
            d[param] = value
        # for
        return d

    @staticmethod
    def _mock_values(_query_params):
        # print('{MockHttp._mock_values}: query_params=%s' % repr(query_params))
        json_data = {"data": "no relevant"}
        return json_data

    def _mock_spreadsheets(self, doc_id, url, query_params):
        if self._verbose:   # pragma: no cover
            print('{MockHttp._mock_sheets}: doc_id=%s, url=%s, query_params=%s' % (repr(doc_id), repr(url), repr(query_params)))
        query_params = self._query_params_to_dict(query_params)

        if url == '':
            json_data = self._mock_list_sheets()
        elif url == 'values:batchGet':
            json_data = self._mock_values(query_params)
        else:       # pragma: no cover
            print('{MockHttp._mock_sheets}: unhandled url: %s' % repr(url))
            json_data = {}

        return json_data

    def request(self, uri, _method="GET", **_kwargs):
        json_data = None
        data = bytearray()
        info = dict()

        if self._next_error is not None:
            error_str, match, error_type = self._next_error
            self._next_error = None

            if error_type == 'socket_timeout':
                raise socket.timeout(error_str)
            elif error_type == 'socket_get_addr_info_error':
                raise socket.gaierror(error_str)
            elif error_type == 'http_error':
                response = Response({})
                response.reason = error_str
                raise HttpError(response, b'')
            elif error_type == 'transport_error':
                raise TransportError(error_str)
            else:       # pragma: no cover
                print('HttpMock.request: unknown error_type %s' % repr(error_type))

        if uri == 'https://oauth2.googleapis.com/token':
            json_data = self._mock_oauth()

        elif uri.startswith('https://sheets.googleapis.com/v4/spreadsheets/'):
            # url/doc_id?query_params
            # url/doc_id/sub?query_params
            url, query_params = uri[46:].split('?')
            pos = url.find('/')
            if pos >= 0:
                doc_id = url[:pos]
                url = url[pos+1:]
            else:
                doc_id = url
                url = ''
            json_data = self._mock_spreadsheets(doc_id, url, query_params)

        else:   # pragma: no cover
            print('{HttpMock.request: unhandled uri: %s' % uri)

        if json_data is not None:       # pragma: no branch
            # convert json (dict) to bytearray
            data = json.dumps(json_data).encode('utf-8')

        response = Response(info)
        return response, data


class TestInstaptoetsCliDownload(E2EHelpers, TestCase):
    """ unittests voor de Instaptoets applicatie, management command download_vragenlijst """

    cli_download = 'download_vragenlijst'

    def setUp(self):
        """ initialisatie van de test case """
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_download(self):
        f1, f2 = self.run_management_command(self.cli_download,
                                             report_exit_code=False)
        self.assertTrue("Error: the following arguments are required: filename" in f1.getvalue())

        fname = os.path.join(self.tmp_dir.name, 'test.json')

        # do a real download
        # f1, f2 = self.run_management_command(self.cli_download, fname,
        #                                      report_exit_code=False)
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))

        my_service = HttpMock(verbose=False)
        with patch('httplib2.Http', return_value=my_service):
            f1, f2 = self.run_management_command(self.cli_download, fname,
                                                 report_exit_code=False)
            self.assertTrue("[INFO] Downloading sheet: 'Sheet1'" in f2.getvalue())

            my_service.prime_error('test1', '', 'socket_timeout')
            f1, f2 = self.run_management_command(self.cli_download, fname,
                                                 report_exit_code=False)
            self.assertTrue('[ERROR] Socket timeout: test1' in f2.getvalue())

            my_service.prime_error('test2', '', 'socket_get_addr_info_error')
            f1, f2 = self.run_management_command(self.cli_download, fname,
                                                 report_exit_code=False)
            self.assertTrue('[ERROR] Socket error: test2' in f2.getvalue())

            my_service.prime_error('test3', '', 'http_error')
            f1, f2 = self.run_management_command(self.cli_download, fname,
                                                 report_exit_code=False)
            self.assertTrue('[ERROR] HttpError: <HttpError 200 "test3">' in f2.getvalue())

            my_service.prime_error('test4', '', 'transport_error')
            f1, f2 = self.run_management_command(self.cli_download, fname,
                                                 report_exit_code=False)
            self.assertTrue('[ERROR] TransportError: test4' in f2.getvalue())


# end of file
