# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from GraphDrive.operations import GraphSite
from GraphDrive.operations.delete import delete_item
from TestHelpers.e2ehelpers import E2EHelpers, OutputBuffer
from unittest.mock import patch
from requests.exceptions import SSLError


class ResponseMock:

    def __init__(self, status_code=200):
        self.status_code = status_code
        self.text = 'mock'
        self.bytes = b'mock bytes'
        self.encoding = 'mock'

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class TestGraphDriveOpDelete(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module delete """

    def test_delete(self):
        item_id = 'item_id'

        # no access token
        out = OutputBuffer()
        site = GraphSite(out)
        with patch('GraphDrive.operations.delete.get_bearer_token', return_value=False):
            delete_item(out, site, 'item_id')
            # print('\nout:', out.getvalue())

        # failure
        out = OutputBuffer()
        site = GraphSite(out)
        with patch('GraphDrive.operations.delete.get_bearer_token', return_value=True):
            with patch('requests.delete', return_value=ResponseMock(status_code=400)):
                delete_item(out, site, item_id)
                self.assertTrue('[ERROR] delete request gaf onverwacht antwoord!' in out.getvalue())

            # exception
            out = OutputBuffer()
            site = GraphSite(out)
            with patch('GraphDrive.operations.delete.requests.delete', side_effect=SSLError('uitzondering')):
                delete_item(out, site, item_id)
            self.assertTrue('[ERROR] {delete_item} Exceptie tijdens delete request: uitzondering' in out.getvalue())

            # accepted
            out = OutputBuffer()
            site = GraphSite(out)
            with patch('GraphDrive.operations.delete.requests.delete', return_value=ResponseMock(status_code=204)):
                delete_item(out, site, item_id)

# end of file
