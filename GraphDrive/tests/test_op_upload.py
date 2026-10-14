# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from GraphDrive.operations import GraphSite
from GraphDrive.operations.upload import upload_file
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from unittest.mock import patch
from requests.exceptions import SSLError
from tempfile import NamedTemporaryFile


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


class TestGraphDriveOpUpload(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module upload """

    def test_list(self):
        local_file = NamedTemporaryFile()       # creates zero-byte file, which is enough
        local_fname = local_file.name
        remote_path = '/remote/folder/'

        # no access token
        out = OutputBuffer()
        site = GraphSite(out)
        with patch('GraphDrive.operations.upload.get_bearer_token', return_value=False):
            res = upload_file(out, site, local_fname, remote_path)
            self.assertIsNone(res)

        with patch('GraphDrive.operations.upload.get_bearer_token', return_value=True):
            with patch('GraphDrive.operations.upload.get_drive_id', return_value=False):
                res = upload_file(out, site, local_fname, remote_path)
                self.assertIsNone(res)

            with patch('GraphDrive.operations.upload.get_drive_id', return_value=True):
                with patch('GraphDrive.operations.upload.requests.put', return_value=ResponseMock(status_code=400)):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res = upload_file(out, site, local_fname, remote_path)
                    self.assertIsNone(res)
                    self.assertTrue('[ERROR] upload request gaf onverwacht antwoord!' in out.getvalue())
                    self.assertTrue(', status_code:400' in out.getvalue())

                with patch('GraphDrive.operations.upload.requests.put', side_effect=SSLError('uitzondering')):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res = upload_file(out, site, local_fname, remote_path)
                    self.assertIsNone(res)
                    self.assertTrue('[ERROR] Exceptie tijdens upload: uitzondering' in out.getvalue())

                with patch('GraphDrive.operations.upload.requests.put', return_value=ResponseMock(status_code=201)):
                    out = OutputBuffer()
                    site = GraphSite(out)
                    res = upload_file(out, site, local_fname, remote_path)
                    self.assertEqual(res, 'OK')


# end of file
