# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Google Sheet wedstrijdformulier openen, inlezen (uitslag) en bijwerken (deelnemerslijst) """

from django.conf import settings
from GoogleDrive.storage_base import StorageError
from googleapiclient.errors import HttpError as GoogleApiError
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
import googleapiclient.errors
import socket
import os.path


# FUTURE: Google Drive API heeft push notification voor wijzigingen

class StorageGoogleSheet:

    SERVICE_ACCOUNT_FILE = os.path.join(settings.CREDENTIALS_PATH,
                                        settings.CREDENTIALS_SERVICE_ACCOUNT_WEDSTRIJDFORMULIEREN)

    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    def __init__(self, stdout):
        self.stdout = stdout
        self._api_spreadsheets = None
        self._api_sheet_values = None
        self._file_id = ""
        self._sheet_name = ""
        self._value_changes = list()
        self._spreadsheet_requests = list()
        self._sheet_name2id = dict()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self._close_api()

    def _setup_api(self):
        if self._api_spreadsheets is None:
            # TODO: exception handling
            creds = Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            service = build('sheets', 'v4', credentials=creds)
            self._api_spreadsheets = service.spreadsheets()          # supports more complex operations, like delete sheet
            self._api_sheet_values = self._api_spreadsheets.values()       # supports value read/writes only

    def _close_api(self):
        for service in (self._api_spreadsheets, self._api_sheet_values):
            if service:
                service.close()
        # for

        self._api_spreadsheets = None
        self._api_sheet_values = None

    def _execute(self, request: HttpRequest) -> dict | None:
        try:
            response = request.execute()
        except socket.timeout as exc:           # pragma: no cover
            self.stdout.write('[ERROR] {execute} Socket timeout: %s' % exc)
        except socket.gaierror as exc:          # pragma: no cover
            # example: [Errno -3] Temporary failure in name resolution
            self.stdout.write('[ERROR] {execute} Socket error: %s' % exc)
        except googleapiclient.errors.HttpError as exc:
            self.stdout.write('[ERROR] {execute} HttpError from API: %s' % exc)
        else:
            # self.stdout.write('[DEBUG] {execute} response=%s' % repr(response))
            return response

        return None

    def _get_sheet_ids(self):
        self._sheet_name2id = dict()

        request = self._api_spreadsheets.get(spreadsheetId=self._file_id,
                                             fields="sheets.properties.title,sheets.properties.sheetId")

        response = self._execute(request)
        if response:
            for sheet in response['sheets']:
                properties = sheet['properties']
                # properties = {'title': 'bla', 'sheetId': 1234}
                self._sheet_name2id[properties['title']] = properties['sheetId']
            # for

        # TODO: raise StorageError in case sheet not accessible

    def selecteer_file(self, file_id):
        self._setup_api()
        self._file_id = file_id
        self._value_changes = list()
        self._spreadsheet_requests = list()
        self._get_sheet_ids()

    def selecteer_sheet(self, sheet_name: str):
        # om spaties te ondersteunen moet de sheet_naam tussen quotes gezet worden
        self._sheet_name = "'" + sheet_name.replace("'", "\\'") + "'"

    def _stuur_value_changes(self):
        if self._value_changes:
            body = {
                "valueInputOption": "RAW",      # just store, do not interpret as number, date, etc.
                "data": self._value_changes,
                "includeValuesInResponse": False,
            }

            request = self._api_sheet_values.batchUpdate(
                                            spreadsheetId=self._file_id,
                                            body=body)

            response = self._execute(request)

            # response is a dict met spreadsheetId, totalUpdated[Rows, Columns, Cells, Sheets] en responses
            # response['responses'] is a lijst met dict, elk met spreadsheetId, updated[Cells, Columns, Rows, Ranges]

            self._value_changes = list()

    def _stuur_spreadsheet_requests(self):
        if self._spreadsheet_requests:
            body = {
                "requests": self._spreadsheet_requests,
            }

            request = self._api_spreadsheets.batchUpdate(
                                    spreadsheetId=self._file_id,
                                    body=body)
            response = self._execute(request)
            # TODO: error propagation

            self._spreadsheet_requests = list()

    def stuur_wijzigingen(self):
        # voor de opgeslagen wijzigingen in een keer door
        # TODO: error propagation
        self._stuur_value_changes()
        self._stuur_spreadsheet_requests()

    def _set_sheet_hidden(self, sheet_name: str, hidden: bool):

        # vertaal de sheet naam naar het sheetId
        sheet_id = self._sheet_name2id[sheet_name]

        request = {
            "updateSheetProperties": {
                "properties": {
                    "sheetId": sheet_id,
                    "hidden": hidden,
                },
                "fields": "hidden"          # welke properties moeten aangepast worden
            }
        }

        self._spreadsheet_requests.append(request)

    def toon_sheet(self, sheet_name: str):
        # hiermee kan een blad getoond worden
        if sheet_name not in self._sheet_name2id:
            raise StorageError('{toon_sheet} Sheet %s niet gevonden in bestand %s' % (repr(sheet_name),
                                                                                      repr(self._file_id)))
        self._set_sheet_hidden(sheet_name, False)

    def hide_sheet(self, sheet_name: str):
        # hiermee kan een blad verstopt worden
        if sheet_name not in self._sheet_name2id:
            raise StorageError('{hide_sheet} Sheet %s niet gevonden in bestand %s' % (repr(sheet_name),
                                                                                      repr(self._file_id)))
        self._set_sheet_hidden(sheet_name, True)

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
        self._value_changes.append(change)

    def get_range(self, range_a1: str) -> list | None:
        # haal de values op in een specifieke range (format: A1:B20) in het huidige sheet
        # geeft een list(rows) terug, met elke row = list(cells)

        request = self._api_sheet_values.get(
                        spreadsheetId=self._file_id,
                        range=self._sheet_name + '!' + range_a1,
                        majorDimension="ROWS",
                        valueRenderOption="UNFORMATTED_VALUE")      # niet aanpassen aan locale

        response = self._execute(request)

        if response:
            # als er geen getallen zijn gevonden in de range, dan is 'values' ook niet aanwezig
            values = response.get('values', [[]])
            # self.stdout.write('[DEBUG] {get_range} values: %s' % repr(values))
        else:
            values = None

        return values

    def clear_range(self, range_a1: str):
        """ wis de cells in de range """
        request = self._api_sheet_values.clear(spreadsheetId=self._file_id,
                                               range=self._sheet_name + '!' + range_a1)
        response = self._execute(request)
        # TODO: error propagation


# end of file
