# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from GoogleDrive.operations import StorageGoogleSheet, StorageError
from TestHelpers.e2ehelpers import E2EHelpers
from googleapiclient.errors import HttpError as GoogleApiError
from httplib2 import Response
from unittest.mock import patch
import io


class GoogleApiSpreadsheetsMock:

    def __init__(self, verbose):
        self.verbose = verbose
        self.next_error = None
        self.next_resp = {}

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.next_error = (error_str, match, error_type)

    def get(self, spreadsheetId: str, fields='', range=None, majorDimension=None, valueRenderOption=None):  # noqa
        if fields:
            sheet = {
                'properties': {
                    'title': 'test',
                    'sheetId': spreadsheetId,
                }
            }
            self.next_resp = {
                'sheets': [sheet]
            }
        else:
            if ":" in range:
                self.next_resp = {
                    'values': [1, 2, 3, 4,5]
                }
            else:
                self.next_resp = None

        return self

    def batchUpdate(self, spreadsheetId, body):             # noqa
        return self

    def clear(self, spreadsheetId, range):                  # noqa
        return self

    def values(self):
        return self

    def execute(self):
        resp = self.next_resp

        if self.next_error is not None:
            error_msg, match, error_type = self.next_error

            if error_type == 'GoogleApiError':
                if self.verbose:    # pragma: no cover
                    print('[DEBUG] {GoogleApiSheetsMock.execute} Generating GoogleApiError (reason=%s)' % repr(error_msg))
                http_resp = Response(info={'status': 400})
                http_resp.reason = error_msg
                self.next_error = None
                raise GoogleApiError(resp=http_resp, content=b'duh')

            else:       # pragma: no cover
                print('[DEBUG] {GoogleApiSheetsMock.execute} Unknown error_type %s' % repr(error_type))

        self.next_resp = {}
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.execute} returning %s' % repr(resp))
        return resp

    def close(self):
        pass


class GoogleApiMock:

    def __init__(self, verbose=False):
        self.spreadsheets_service = GoogleApiSpreadsheetsMock(verbose)

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.spreadsheets_service.prime_error(error_str, match, error_type)

    def spreadsheets(self):
        return self.spreadsheets_service


class TestGoogleDriveStorageSheets(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, operations storage_sheets """

    def test_open(self):
        out = OutputWrapper(io.StringIO())

        # einde van "with" roept __exit__ aan
        with StorageGoogleSheet(out) as sheet:
            pass

        # einde van "with" roept __exit__ aan
        with StorageGoogleSheet(out) as sheet:
            my_service = GoogleApiMock(verbose=True)
            with patch('GoogleDrive.operations.storage_sheets.build', return_value=my_service):
                sheet.selecteer_file('x')
                sheet.selecteer_file('x')       # tweede keer is anders in setup_api
                sheet.selecteer_sheet("Test 'Sheet'")

        # error handling
        my_service.prime_error('test', '', 'GoogleApiError')
        with patch('GoogleDrive.operations.storage_sheets.build', return_value=my_service):
            sheet.selecteer_file('x')

    def test_spreadsheet_actions(self):
        out = OutputWrapper(io.StringIO())

        # einde van "with" roept __exit__ aan
        with StorageGoogleSheet(out) as sheet:
            my_service = GoogleApiMock(verbose=False)
            with patch('GoogleDrive.operations.storage_sheets.build', return_value=my_service):
                sheet.selecteer_file('x')
                sheet.toon_sheet('test')
                sheet.hide_sheet('test')
                with self.assertRaises(StorageError) as exc:
                    sheet.toon_sheet('fail')
                with self.assertRaises(StorageError) as exc:
                    sheet.hide_sheet('fail')

                sheet.stuur_wijzigingen()

    def test_range(self):
        # range actions are executed without queuing
        out = OutputWrapper(io.StringIO())

        # einde van "with" roept __exit__ aan
        with StorageGoogleSheet(out) as sheet:
            my_service = GoogleApiMock(verbose=True)
            with patch('GoogleDrive.operations.storage_sheets.build', return_value=my_service):
                sheet.selecteer_file('x')

                res = sheet.get_range('A1:A5')
                self.assertIsNotNone(res)

                res = sheet.get_range('error')
                self.assertIsNone(res)

                sheet.clear_range('A1:A5')

    def test_value_actions(self):
        # value actions are queued up
        out = OutputWrapper(io.StringIO())

        # einde van "with" roept __exit__ aan
        with StorageGoogleSheet(out) as sheet:
            my_service = GoogleApiMock(verbose=False)
            with patch('GoogleDrive.operations.storage_sheets.build', return_value=my_service):
                sheet.selecteer_file('x')
                sheet.clear_range('A1:A5')
                sheet.wijzig_cellen('A1:A5', [1, 2, 3, 4, 5])
                sheet.stuur_wijzigingen()

# end of file
