# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van bestanden in een folder structuur in Google Drive """

from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os


class MonitorDriveFiles:

    # service account dat gebruikt wordt om te downloaden (moet view rechten hebben op het document)
    SERVICE_ACCOUNT_FILE = os.path.join(settings.CREDENTIALS_PATH,
                                        settings.CREDENTIALS_SERVICE_ACCOUNT_WEDSTRIJDFORMULIEREN)

    # Scopes that allow to edit, create, delete and share all of the owners' google drive files
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, stdout):
        self.stdout = stdout
        self._service_files = None

        self._setup_service()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self._close_services()

    def _setup_service(self):
        if not self._service_files:
            creds = Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            service = build('drive', 'v3', credentials=creds)
            self._service_files = service.files()

    def _close_services(self):
        for service in (self._service_files,):
            if service:
                service.close()
        # for
        self._service_files = None

    def get_laatste_wijziging(self, file_id):
        # self.stdout.write('[DEBUG] {get_laatste_wijziging} file_id=%s' % repr(file_id))

        fields = "modifiedTime,lastModifyingUser(displayName,emailAddress)"
        request = self._service_files.get(fileId=file_id, fields=fields)
        resp = request.execute()
        # self.stdout.write('[DEBUG] resp: %s' % repr(resp))

        if resp:
            op = resp['modifiedTime']
            door = (resp['lastModifyingUser'].get('displayName', '') or
                    resp['lastModifyingUser'].get('emailAddress', '') or    # if present, in case displayName is empty
                    'Anoniem')                                              # fallback
        else:
            op = door = ''

        return op, door


# end of file
