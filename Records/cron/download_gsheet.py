# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" Download de Nationale Records administratie uit gsheets """

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import settings_local
import hashlib
import json

OUTFILE = '/tmp/downloader/records.json'

# service account dat gebruikt wordt om te downloaden (moet view rechten hebben op het document)
SERVICE_ACCOUNT_FILE = '/tmp/downloader/service-account.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

print("[INFO] Nationale Records downloader service")

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gsheets_api = build('sheets', 'v4', credentials=creds).spreadsheets()

# door de naam van een sheet te gebruiken as 'Range' krijg je alle cellen uit de sheet
request = gsheets_api.values().batchGet(
                spreadsheetId=settings_local.RECORDS_GSHEET_FILE_ID,
                ranges=settings_local.RECORDS_GSHEET_SHEET_NAMES)
result = request.execute()

with open(OUTFILE, "w", encoding='utf-8') as jsonfile:
    json.dump(result, jsonfile, ensure_ascii=False)

print('[INFO] Written ' + OUTFILE)

# end of file
