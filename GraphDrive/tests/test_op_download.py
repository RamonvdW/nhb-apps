# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from GraphDrive.operations.download import download
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
from requests.exceptions import SSLError
import io


class ResponseMock:

    def __init__(self, status_code=200, has_value=True, multiple_drives=False, set_web_url=False):
        self.status_code = status_code
        self.text = 'mock'
        self.bytes = b'mock bytes'
        self.encoding = 'mock'
        self._has_value = has_value
        self._multiple_drives = multiple_drives
        self._set_web_url = set_web_url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter_content(self, chunk_size=1024):
        return iter([self.bytes])


class TestGraphDriveOpDownload(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module download """

    def setUp(self):
        self.test_fname = '/tmp/local'

    def test_download(self):

        # no access token
        with patch('GraphDrive.operations.download.get_bearer_token', return_value=''):
            out = OutputWrapper(io.StringIO())
            local_fname = download(out, 'remote', self.test_fname)
            self.assertIsNone(local_fname)
            # print('\nout:', out.getvalue())

        with patch('GraphDrive.operations.download.get_bearer_token', return_value='token'):
            with patch('GraphDrive.operations.download.get_drive_id', return_value=('', '')):
                out = OutputWrapper(io.StringIO())
                local_fname = download(out, 'remote', self.test_fname)
                self.assertIsNone(local_fname)
                # print('\nout:', out.getvalue())

        with patch('GraphDrive.operations.download.get_bearer_token', return_value='token'):
            with patch('GraphDrive.operations.download.get_drive_id', return_value=('drive', '')):

                # connection error
                out = OutputWrapper(io.StringIO())
                with patch('requests.get', side_effect=SSLError('uitzondering')):
                    local_fname = download(out, 'remote', self.test_fname)
                    self.assertIsNone(local_fname)
                # print('\nout:', out.getvalue())
                self.assertTrue('[ERROR] Exceptie tijdens download: uitzondering' in out.getvalue())

                # status code != 200
                rsp = ResponseMock(status_code=404)
                out = OutputWrapper(io.StringIO())
                with patch('requests.get', return_value=rsp):
                    local_fname = download(out, 'remote', self.test_fname)
                    self.assertIsNone(local_fname)
                # print('\nout:', out.getvalue())
                self.assertTrue("[ERROR] download request gaf onverwacht antwoord! response encoding:'mock', status_code:404" in out.getvalue())

                rsp = ResponseMock(status_code=200)
                out = OutputWrapper(io.StringIO())
                with patch('requests.get', return_value=rsp):
                    local_fname = download(out, 'remote', self.test_fname)
                    self.assertEqual(local_fname, self.test_fname)


# end of file
