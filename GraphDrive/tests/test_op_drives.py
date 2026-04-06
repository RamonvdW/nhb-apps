# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from django.core.management.base import OutputWrapper
from GraphDrive.operations.drives import clear_drives_cache, get_drive_id
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch
from requests.exceptions import SSLError
from datetime import timedelta
import io


class ResponseMock:

    def __init__(self, status_code=200, has_value=True, multiple_drives=False, set_web_url=False):
        self.status_code = status_code
        self.text = 'mock'
        self.encoding = 'mock'
        self._has_value = has_value
        self._multiple_drives = multiple_drives
        self._set_web_url = set_web_url

    def json(self):
        drive = {
            'id': 'drive1',
        }
        if self._set_web_url:
            drive['webUrl'] = 'some test url'

        d = {
            'value': [drive],
        }

        if self._multiple_drives:
            d['value'].append({'id': 'drive2'})

        if not self._has_value:
            del d['value']
            d['heeft_geen_value'] = True

        return d


class TestGraphDriveOpDrives(E2EHelpers, TestCase):
    """ unittests voor de GraphDrive applicatie, operations module drives """

    def test_drives(self):
        clear_drives_cache()

        # no access token
        with patch('GraphDrive.operations.drives.get_bearer_token', return_value=''):
            out = OutputWrapper(io.StringIO())
            drive_id, drive_web_url = get_drive_id(out)
            self.assertEqual(drive_id, drive_web_url, '')
            # print('\nout:', out.getvalue())
            self.assertTrue('[ERROR] {drives} No access token' in out.getvalue())
            self.assertTrue('[ERROR] No drives' in out.getvalue())

        # exception
        with patch('GraphDrive.operations.access_token.get_bearer_token', return_value='test token'):
            out = OutputWrapper(io.StringIO())
            with patch('requests.get', side_effect=SSLError('uitzondering')):
                drive_id, drive_web_url = get_drive_id(out)
                self.assertEqual(drive_id, drive_web_url, '')
            # print('\nout:', out.getvalue())
            self.assertTrue('[ERROR] Exceptie bij versturen get_drive_id request: uitzondering' in out.getvalue())
            self.assertTrue('[ERROR] No drives' in out.getvalue())

            # foutcode
            out = OutputWrapper(io.StringIO())
            resp = ResponseMock(status_code=404)
            with patch('requests.get', return_value=resp):
                drive_id, drive_web_url = get_drive_id(out)
            # print('\nout:', out.getvalue())
            self.assertTrue("[ERROR] Get drive id request gaf onverwacht antwoord!" in out.getvalue())
            self.assertTrue('[ERROR] No drives' in out.getvalue())

            # niet compleet (1)
            out = OutputWrapper(io.StringIO())
            resp = ResponseMock(has_value=False)
            with patch('requests.get', return_value=resp):
                drive_id, drive_web_url = get_drive_id(out)
            # print('\nout:', out.getvalue())
            self.assertTrue("[ERROR] Missing value in response: {'heeft_geen_value': True}" in out.getvalue())
            self.assertTrue('[ERROR] No drives' in out.getvalue())

            # meerdere drives
            out = OutputWrapper(io.StringIO())
            resp = ResponseMock(multiple_drives=True)
            with patch('requests.get', return_value=resp):
                drive_id, drive_web_url = get_drive_id(out)
            # print('\nout:', out.getvalue())
            self.assertTrue("[ERROR] Expected 1 drive but got 2" in out.getvalue())
            self.assertTrue("Drive: {'id': 'drive1'}" in out.getvalue())
            self.assertTrue("Drive: {'id': 'drive2'}" in out.getvalue())

            # drive niet compleet
            out = OutputWrapper(io.StringIO())
            resp = ResponseMock()
            with patch('requests.get', return_value=resp):
                drive_id, drive_web_url = get_drive_id(out)
            # print('\nout:', out.getvalue())
            self.assertTrue("[ERROR] Not a complete drive response: {'id': 'drive1'}" in out.getvalue())

            # goed
            out = OutputWrapper(io.StringIO())
            resp = ResponseMock(set_web_url=True)
            with patch('requests.get', return_value=resp):
                drive_id, drive_web_url = get_drive_id(out)
                self.assertEqual(drive_id, 'drive1')
                self.assertEqual(drive_web_url, 'some test url')
            # print('\nout:', out.getvalue())
            self.assertFalse("[ERROR]" in out.getvalue())

        # get cached result
        out = OutputWrapper(io.StringIO())
        drive_id, drive_web_url = get_drive_id(out)
        self.assertEqual(drive_id, 'drive1')
        self.assertEqual(drive_web_url, 'some test url')
        # print('\nout:', out.getvalue())
        self.assertFalse("[ERROR]" in out.getvalue())

# end of file
