# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Download de Instaptoets vragen uit gsheets """
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import googleapiclient.errors
import google.auth.exceptions
import settings_local
import socket
import json

OUTFILE = '/tmp/downloader/instaptoets.json'

# service account dat gebruikt wordt om te downloaden (moet view rechten hebben op het document)
SERVICE_ACCOUNT_FILE = '/tmp/downloader/service-account.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

print("[INFO] Instaptoets downloader service")

try:
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gsheets_api = build('sheets', 'v4', credentials=creds).spreadsheets()

    try:
        # haal alle sheet names op
        sheet_names = list()
        request = gsheets_api.get(spreadsheetId=settings_local.INSTAPTOETS_GSHEET_FILE_ID,
                                  includeGridData=False)        # not the actual data, just the structure
        result = request.execute()
        print('[DEBUG] result: %s' % repr(result))
        for sheet in result['sheets']:
            sheet_names.append(sheet['properties']['title'])
        # for
        print('[DEBUG] sheet_names: %s' % repr(sheet_names))

        # door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
        sheets = dict()
        for sheet_name in sheet_names:
            request = gsheets_api.values().batchGet(
                            spreadsheetId=settings_local.INSTAPTOETS_GSHEET_FILE_ID,
                            ranges=sheet_name)
            sheets[sheet_name] = request.execute()
        # for
    except socket.timeout as exc:
        print('[ERROR] Socket timeout: %s' % exc)
    except socket.gaierror as exc:
        # example: [Errno -3] Temporary failure in name resolution
        print('[ERROR] Socket error: %s' % exc)
    except googleapiclient.errors.HttpError as exc:
        print('[ERROR] HttpError from API: %s' % exc)
    else:
        with open(OUTFILE, "w", encoding='utf-8') as jsonfile:
            json.dump(sheets, jsonfile, ensure_ascii=False)

        print('[INFO] Written ' + OUTFILE)

except google.auth.exceptions.TransportError as exc:
    print('[ERROR] Error downloading gsheet: %s' % str(exc))

# end of file
