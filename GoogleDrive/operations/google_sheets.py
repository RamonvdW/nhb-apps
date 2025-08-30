# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Google Sheet wedstrijdformulier openen, inlezen (uitslag) en bijwerken (deelnemerslijst) """

from django.utils import timezone
from googleapiclient.errors import HttpError as GoogleApiError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import googleapiclient.errors
import socket


# FUTURE: Google Drive API heeft push notification voor wijzigingen

class GoogleSheet:

    SERVICE_ACCOUNT_FILE = '/tmp/mh_wedstrijdformulieren_service-account.json'

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, stdout):
        self.stdout = stdout
        self._gsheets_api = None
        self._file_id = ""
        self._sheet_name = ""
        self._changes = list()

    def _connect(self):
        if self._gsheets_api is None:
            # TODO: exception handling
            creds = Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            service = build('sheets', 'v4', credentials=creds)
            self._gsheets_api = service.spreadsheets()          # supports more complex operations, like delete sheet
            self._values_api = self._gsheets_api.values()       # supports value read/writes only

    def selecteer_file(self, file_id):
        self._connect()
        self._file_id = file_id
        self._changes = list()

    def selecteer_sheet(self, sheet_name: str):
        self._sheet_name = sheet_name

    def wijzig_cellen(self, range_a1: str, values: list):
        """
            range_a1: "A1:D5"       # A1 notation
            values_list: [
                        ["val", "val", "val", "val"],   # values for row 1, columns A, B, C, D
                        ["val", "val", "val", "val"],   # values for row 2, columns A, B, C, D
                        # etc.
                    ]
        """
        change = {
            "range": self._sheet_name + '!' + range_a1,
            "values": values,
            "majorDimension": "ROWS",
        }
        self._changes.append(change)

    def execute(self):
        # voor de opgeslagen wijzigingen in een keer door

        body = {
            "valueInputOption": "RAW",      # just store, do not interpret as number, date, etc.
            "data": self._changes,
            "includeValuesInResponse": False,
        }

        request = self._values_api.batchUpdate(
                                        spreadsheetId=self._file_id,
                                        body=body)
        try:
            response = request.execute()
        except socket.timeout as exc:
            print('[ERROR] {execute} Socket timeout: %s' % exc)
        except socket.gaierror as exc:
            # example: [Errno -3] Temporary failure in name resolution
            print('[ERROR] {execute} Socket error: %s' % exc)
        except googleapiclient.errors.HttpError as exc:
            print('[ERROR] {execute} HttpError from API: %s' % exc)
        else:
            print('[DEBUG] {execute} response=%s' % repr(response))

    def delete_sheet(self):
        # hiermee kan een blad verwijderd worden, bijvoorbeeld een finales blad
        pass


# end of file
