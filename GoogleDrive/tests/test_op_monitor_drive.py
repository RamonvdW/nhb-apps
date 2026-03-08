# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from GoogleDrive.operations import MonitorDriveFiles
from TestHelpers.e2ehelpers import E2EHelpers
from googleapiclient.errors import HttpError as GoogleApiError
from httplib2 import Response
from unittest.mock import patch
import datetime
import io


class GoogleApiFilesMock:

    def __init__(self, verbose):
        self.verbose = verbose
        self.next_resp = {}
        self.next_error = None

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.next_error = (error_str, match, error_type)

    def get(self, fileId: str, fields: list):
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.get} body=%s, kwargs=%s' % (repr(fileId), repr(fields)))

        if fileId == 'file_user':
            self.next_resp = {
                'modifiedTime': '2099-01-01T00:00:00.000000',       # somewhere in the future
                'lastModifyingUser': {
                    'displayName': 'User',
                    'emailAddress': 'user@khsn.not',
                },
            }

        if fileId == 'file_email':
            self.next_resp = {
                'modifiedTime': '2099-01-01T00:00:00.000000',       # somewhere in the future
                'lastModifyingUser': {
                    'emailAddress': 'user@khsn.not',
                },
            }

        if fileId == 'file_anonymous':
            self.next_resp = {
                'modifiedTime': '2099-01-01T00:00:00.000000',       # somewhere in the future
            }

        return self

    def execute(self):
        resp = self.next_resp

        if self.next_error is not None:
            error_msg, match, error_type = self.next_error

            if error_type == 'GoogleApiError':
                if self.verbose:    # pragma: no cover
                    print('[DEBUG] {GoogleApiFilesMock.execute} Generating GoogleApiError (reason=%s)' % repr(error_msg))
                http_resp = Response(info={'status': 400})
                http_resp.reason = error_msg
                # self.next_error = None        # nodig voor retry
                raise GoogleApiError(resp=http_resp, content=b'duh')

            else:       # pragma: no cover
                print('[DEBUG] {GoogleApiFilesMock.execute} Unknown error_type %s' % repr(error_type))

        self.next_resp = {}
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.execute} returning %s' % repr(resp))
        return resp

    def close(self):
        pass


class GoogleApiMock:

    def __init__(self, verbose=False):
        self.files_service = GoogleApiFilesMock(verbose)

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.files_service.prime_error(error_str, match, error_type)

    def files(self):
        return self.files_service


class TestGoogleDriveOpMonitorDrive(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, operations monitor_drive """

    def test_laatste_wijziging(self):
        out = OutputWrapper(io.StringIO())

        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.monitor_drive.build', return_value=my_service):
            # einde van "with" roept __exit__ aan
            with MonitorDriveFiles(out, retry_delay=0.001) as drive:
                op, door = drive.get_laatste_wijziging('file_user')
                # print('op=%s, door=%s' % (repr(op), repr(door)))
                self.assertTrue(isinstance(op, datetime.datetime))
                self.assertEqual(door, 'User')

                op, door = drive.get_laatste_wijziging('file_email')
                self.assertTrue(isinstance(op, datetime.datetime))
                self.assertEqual(door, 'user@khsn.not')

                op, door = drive.get_laatste_wijziging('file_anonymous')
                self.assertTrue(isinstance(op, datetime.datetime))
                self.assertEqual(door, 'Anoniem')

                my_service.prime_error('test A', '-', 'GoogleApiError')
                op, door = drive.get_laatste_wijziging('file_user')
                self.assertTrue(op == door == '')

# end of file
