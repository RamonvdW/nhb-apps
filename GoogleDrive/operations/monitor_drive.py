# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van bestanden in een folder structuur in Google Drive """

from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError as GoogleApiError
from googleapiclient.http import HttpRequest
from google.oauth2.service_account import Credentials
import socket
import time
import os


class MonitorDriveFiles:

    # service account dat gebruikt wordt om te downloaden (moet view rechten hebben op het document)
    SERVICE_ACCOUNT_FILE = os.path.join(settings.CREDENTIALS_PATH,
                                        settings.CREDENTIALS_SERVICE_ACCOUNT_WEDSTRIJDFORMULIEREN)

    # Scopes that allow to edit, create, delete and share all of the owners' google drive files
    SCOPES = ['https://www.googleapis.com/auth/drive']

    def __init__(self, stdout, retry_delay:float=1.0):
        self.stdout = stdout
        self._service_files = None
        self._retry_delay = retry_delay

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

    def _execute(self, request: HttpRequest) -> dict | None:
        retries = 7
        wait_sec = self._retry_delay
        while retries > 0:
            try:
                response = request.execute()
            except socket.timeout as exc:           # pragma: no cover
                self.stdout.write('[ERROR] {execute} Socket timeout: %s' % exc)
            except socket.gaierror as exc:          # pragma: no cover
                # example: [Errno -3] Temporary failure in name resolution
                self.stdout.write('[ERROR] {execute} Socket error: %s' % exc)
            except GoogleApiError as exc:           # aka HttpError
                self.stdout.write('[ERROR] {execute} GoogleApiError: %s' % exc)
            else:
                # self.stdout.write('[DEBUG] {execute} response=%s' % repr(response))
                return response

            self.stdout.write('[DEBUG] {execute} Retrying in %s seconds' % wait_sec)

            time.sleep(wait_sec)
            wait_sec *= 2       # 1, 2, 4, 8, 16, 32, 64
            retries -= 1
        # while

        return None

    def get_laatste_wijziging(self, file_id):
        # self.stdout.write('[DEBUG] {get_laatste_wijziging} file_id=%s' % repr(file_id))

        fields = "modifiedTime,lastModifyingUser(displayName,emailAddress)"
        request = self._service_files.get(fileId=file_id, fields=fields)
        resp = self._execute(request)
        self.stdout.write('[DEBUG] resp: %s' % repr(resp))

        op = door = ''
        if resp:
            op = resp.get('modifiedTime', '')
            last_user = resp.get('lastModifyingUser', None)
            if last_user and isinstance(last_user, dict):
                door = (last_user.get('displayName', '') or
                        last_user.get('emailAddress', '') or    # if present, in case displayName is empty
                        'Anoniem')                              # fallback

        return op, door


# end of file
