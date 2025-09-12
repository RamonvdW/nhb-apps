# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Nederlandse Records gsheet downloaden en als JSON opslaan op disk """

from django.conf import settings
from django.core.management.base import BaseCommand
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import googleapiclient.errors
import google.auth.exceptions
import socket
import json

# service account dat gebruikt wordt om te downloaden (moet view rechten hebben op het document)
SERVICE_ACCOUNT_FILE = settings.CREDENTIALS_PATH + 'mh-downloader_service-account.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class Command(BaseCommand):
    help = "Download de instaptoets vragenlijst gsheet"

    def __init__(self):
        super().__init__()
        self._gsheets_api = None

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, help="onder deze naam opslaan")

    def _setup_api(self):
        # TODO: exception handling
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        self._gsheets_api = build('sheets', 'v4', credentials=creds).spreadsheets()

    def _download(self):
        try:
            # haal alle sheet names op
            sheet_names = list()
            request = self._gsheets_api.get(
                                    spreadsheetId=settings.INSTAPTOETS_GSHEET_FILE_ID,
                                    includeGridData=False)  # not the actual data, just the structure
            result = request.execute()
            # self.stdout.write('[DEBUG] result: %s' % repr(result))
            for sheet in result['sheets']:
                sheet_names.append(sheet['properties']['title'])
            # for
            self.stdout.write('[INFO] Downloading %s sheets' % len(sheet_names))

            # door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
            sheets = dict()
            for sheet_name in sheet_names:
                self.stdout.write('[INFO] Downloading sheet: %s' % repr(sheet_name))
                request = self._gsheets_api.values().batchGet(
                                        spreadsheetId=settings.INSTAPTOETS_GSHEET_FILE_ID,
                                        ranges=sheet_name)
                sheets[sheet_name] = request.execute()
            # for
            return sheets

        except socket.timeout as exc:
            self.stdout.write('[ERROR] Socket timeout: %s' % exc)
        except socket.gaierror as exc:
            # example: [Errno -3] Temporary failure in name resolution
            self.stdout.write('[ERROR] Socket error: %s' % exc)
        except googleapiclient.errors.HttpError as exc:
            self.stdout.write('[ERROR] HttpError from API: %s' % exc)
        except google.auth.exceptions.TransportError as exc:
            self.stdout.write('[ERROR] Error downloading gsheet: %s' % str(exc))

        return None

    def _save_json(self, fname: str, data):
        self.stdout.write('[INFO] Saving to %s' % repr(fname))

        with open(fname, "w", encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, ensure_ascii=False)

    def handle(self, *args, **options):
        self.stdout.write("[INFO] Instaptoets downloader service")

        self._setup_api()

        data = self._download()
        if data:
            fname = options['filename'][0]
            self._save_json(fname, data)

# end of file
