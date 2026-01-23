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
                                        settings.CREDENTIALS_SERVICE_ACCOUNT_DOWNLOADER)

    # Scopes that allow to edit, create, delete and share all of the owners' google drive files
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, stdout):
        self.stdout = stdout
        self._service_revisions = None

        self._setup_service()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self._close_services()

    def _setup_service(self):
        if not self._service_revisions:
            creds = Credentials.from_service_account_file(self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES)
            service = build('drive', 'v3', credentials=creds)
            self._service_revisions = service.revisions()

    def _close_services(self):
        for service in (self._service_revisions,):
            if service:
                service.close()
        # for
        self._service_revisions = None

    def get_laatste_wijziging(self, file_id):
        # self.stdout.write('{get_laatste_wijziging} file_id=%s' % repr(file_id))
        fields = "revisions(id,modifiedTime,lastModifyingUser(displayName,emailAddress))"
        request = self._service_revisions.list(fileId=file_id, fields=fields)
        resp = request.execute()
        # print('resp: %s' % repr(resp))

        if resp:
            revisions = resp.get('revisions', [])
            order = list()
            for revision in revisions:
                tup = (revision['modifiedTime'], revision)
                order.append(tup)
            # for
            if len(order):
                order.sort(reverse=True)        # newest first
                newest_revision = order[0][-1]
                # print(newest_revision)
                op = newest_revision['modifiedTime']
                door = (newest_revision['lastModifyingUser'].get('displayName', '') or
                        newest_revision['lastModifyingUser'].get('emailAddress', '') or
                        'Anoniem')
                return op, door

        return '', ''

# end of file
