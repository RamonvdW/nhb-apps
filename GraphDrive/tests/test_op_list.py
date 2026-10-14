# -*- coding: utf-8 -*-
import requests.cookies
#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from GraphDrive.operations import GraphSite
from GraphDrive.operations.list import list_folders_and_files
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from unittest.mock import patch
from requests.exceptions import SSLError
from datetime import timedelta


class ResponseMock:

    def __init__(self, status_code=200, heeft_value=True):
        self.status_code = status_code
        self.text = 'mock'
        self.bytes = b'mock bytes'
        self.encoding = 'mock'
        self._heeft_value = heeft_value
        self._files = [{'folder': True, 'name': 'folder_name'},
                       {'name': 'file1', 'size': '1', 'id': 'item_id1', 'lastModifiedDateTime': 'stamp1'}]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def json(self):
        d = {}
        if self._heeft_value:
            d['value'] = self._files
        return d


class TestGraphDriveOpList(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module list """

    def test_list(self):
        folder_name = '/remote/folder/'

        # no access token
        out = OutputBuffer()
        site = GraphSite(out)
        with patch('GraphDrive.operations.list.get_bearer_token', return_value=False):
            res = list_folders_and_files(out, site, folder_name)
            self.assertEqual(res, (None, None))

        with patch('GraphDrive.operations.list.get_bearer_token', return_value=True):
            with patch('GraphDrive.operations.list.get_drive_id', return_value=False):
                res = list_folders_and_files(out, site, folder_name)
                self.assertEqual(res, (None, None))

            with patch('GraphDrive.operations.list.get_drive_id', return_value=True):
                with patch('GraphDrive.operations.list.requests.get', return_value=ResponseMock(status_code=400)):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res = list_folders_and_files(out, site, folder_name)
                    self.assertEqual(res, (None, None))
                    self.assertTrue('[ERROR] list request gaf onverwacht antwoord!' in out.getvalue())
                    self.assertTrue(', status_code:400' in out.getvalue())

                with patch('GraphDrive.operations.download.requests.get', side_effect=SSLError('uitzondering')):
                    res = list_folders_and_files(out, site, folder_name)
                    self.assertEqual(res, (None, None))
                    self.assertTrue('[ERROR] {list_folders_and_files} Exceptie tijdens get request: uitzondering' in out.getvalue())

                with patch('GraphDrive.operations.list.requests.get', return_value=ResponseMock(heeft_value=False)):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res = list_folders_and_files(out, site, folder_name)
                    self.assertEqual(res, (None, None))
                    # print(out.getvalue())
                    self.assertTrue('[ERROR] Missing value in response' in out.getvalue())

                with patch('GraphDrive.operations.list.requests.get', return_value=ResponseMock()):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res1, res2 = list_folders_and_files(out, site, folder_name)
                    # print(out.getvalue())
                    self.assertEqual(res1, ['folder_name'])
                    self.assertEqual(res2, [('stamp1', '1', 'file1', 'item_id1'),])


# end of file
