# -*- coding: utf-8 -*-

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van bestanden in een folder structuur in Google Drive """

from django.utils import timezone
from GoogleDrive.models import Token, Bestand
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError as GoogleApiError
from googleapiclient.http import HttpRequest
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from GoogleDrive.storage_base import StorageBase, StorageError
import traceback
import socket
import json
import time
import sys
import os


class StorageGoogleDrive(StorageBase):

    """ let op: genereert StorageError exception """

    # Scopes that allow to edit, create, delete and share all of the owners' google drive files
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # MIME types for items in a Google Driver folder
    MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'
    MIME_TYPE_SHEET = 'application/vnd.google-apps.spreadsheet'

    def __init__(self, stdout, begin_jaar: int, share_with_emails: list, retry_delay:float=1.0):
        super().__init__(stdout, begin_jaar, share_with_emails)

        self._creds = None
        self._service_files = None
        self._service_perms = None
        self._retry_delay = retry_delay

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_val, _exc_tb):
        self._close_service()

    @staticmethod
    def _load_credentials_json():
        token = (Token
                 .objects
                 .order_by('-when')     # nieuwste eerst
                 .first())
        if not token:
            raise StorageError('No token')

        js_data = json.loads(token.creds)
        return js_data

    def check_access(self):
        # google api libs refresh the token automatically
        js_data = self._load_credentials_json()
        try:
            self._creds = Credentials.from_authorized_user_info(js_data)
        except ValueError as exc:
            raise StorageError('Invalid credentials: %s' % str(exc))
        # TODO: try to trigger refresh and check validity of the token
        # typische foutmelding:
        #   [ERROR] StorageError: {google_drive} RefreshError:
        #   ('invalid_grant: Token has been expired or revoked.',
        #    {'error': 'invalid_grant',
        #     'error_description': 'Token has been expired or revoked.'
        #     }
        #    )
        return self._creds.refresh_token

    def _setup_service(self):
        service = build("drive", "v3", credentials=self._creds)
        self._service_files = service.files()
        self._service_perms = service.permissions()

    def _close_service(self):
        """ disconnect the persistent http2 connections """
        for service in (self._service_files, self._service_perms):
            if service:
                service.close()
        # for
        self._service_files = None
        self._service_perms = None

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

    def _maak_folder(self, parent_folder_id, folder_name):
        file_metadata = {
            "name": folder_name,
            "mimeType": self.MIME_TYPE_FOLDER,
            "parents": [parent_folder_id],
        }
        request = self._service_files.create(body=file_metadata, fields='id')   # fields is comma-separated

        response = self._execute(request)

        if response:
            folder_id = response['id']
            return folder_id

        raise StorageError('{maak_folder} Failed to create folder %s in parent %s' % (repr(folder_name),
                                                                                      repr(parent_folder_id)))

    def _vind_globale_folder(self, folder_name):
        query = "mimeType='%s'" % self.MIME_TYPE_FOLDER
        query += " and trashed=false"
        query += " and name='%s'" % folder_name
        request = self._service_files.list(q=query)

        response = self._execute(request)
        # print('[DEBUG] {vind_globale_folder} response:', response)

        if not (response and 'files' in response):
            raise StorageError("{vind_globale_folder} Missing 'files' in response")

        all_files = response['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            # self.stdout.write('first_file: %s' % repr(first_file))
            folder_id = first_file['id']
        else:
            # niet gevonden
            folder_id = None
        return folder_id

    def _list_folder(self, parent_folder_id, folders_only=False):
        # haalt de inhoud van een folder op
        # retourneer een dictionary: ["name"] = id
        query = "'%s' in parents" % parent_folder_id
        query += " and trashed=false"
        if folders_only:
            query += " and mimeType='%s'" % self.MIME_TYPE_FOLDER
        request = self._service_files.list(q=query)

        response = self._execute(request)
        # print('[DEBUG] list folder response:', response)

        if not (response and 'files' in response):
            raise StorageError("{list_folder} No 'files' in response")

        out = {obj['name']: obj['id']
               for obj in response['files']}
        return out

    def _share_seizoen_folder(self):
        if self._folder_id_seizoen:
            # request = self._service_files.get(fileId=self._folder_id_seizoen)
            # response = self._execute(request)
            # print('{share_seizoen_folder} files.get response=%s' % repr(response))

            request = self._service_perms.list(fileId=self._folder_id_seizoen,
                                               fields="permissions(id, role, type, emailAddress)")

            response = self._execute(request)
            # self.stdout.write('[INFO] {share_seizoen_folder} perms.list response=%s' % repr(response))

            share_with = self._share_with_emails[:]
            for perm in response['permissions']:
                if perm['type'] == 'user' and perm['emailAddress'] in share_with:
                    # already shared with this user
                    # remove from list to prevent sharing again
                    share_with.remove(perm['emailAddress'])
            # for

            # add new sharing permissions
            for email in share_with:
                request = self._service_perms.create(fileId=self._folder_id_seizoen,
                                                     body={
                                                         "type": "user",
                                                         "role": "writer",
                                                         "emailAddress": email,
                                                     },
                                                     sendNotificationEmail=False)
                response = self._execute(request)
                # self.stdout.write('[INFO] {share_seizoen_folder} perms.create response=%s' % repr(response))
            # for

    def _vind_comp_bestand(self, folder_name, fname) -> str:
        folder_id_comp = self._comp2folder_id.get(folder_name, None)
        if not folder_id_comp:
            raise StorageError('Folder %s niet gevonden' % repr(folder_name))

        query = "name='%s'" % fname
        query += " and '%s' in parents" % folder_id_comp
        query += " and mimeType='%s'" % self.MIME_TYPE_SHEET
        request = self._service_files.list(q=query)

        response = self._execute(request)
        # self.stdout.write('[DEBUG] {vind_comp_bestand} response: %s' % repr(response))

        all_files = response['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            return first_file['id']
        return ""

    def _maak_bestand_uit_template(self, folder_name, fname) -> str:
        # kopieer een template naar een nieuw bestand
        # print('[DEBUG] {google_drive.maak_bestand_uit_template} folder_name=%s, fname=%s' % (repr(folder_name),
        #                                                                                      repr(fname)))

        # bepaal de directory waar het bestand in aangemaakt moet worden
        folder_id = self._comp2folder_id.get(folder_name, None)
        if not folder_id:
            raise StorageError('{maak_bestand_uit_template} Folder met naam %s niet gevonden' % repr(folder_name))

        # bepaal de template die gebruikt moet worden
        template_file_id = self._comp2template_file_id.get(folder_name, None)
        if not template_file_id:
            raise StorageError('{maak_bestand_uit_template} Geen template_file_id voor folder %s' % repr(folder_name))

        request = self._service_files.copy(fileId=template_file_id,
                                           body={"parents": [folder_id],
                                                 "name": fname})

        response = self._execute(request)
        # self.stdout.write('[DEBUG] {maak_bestand_uit_template} files copy result is %s' % repr(result))

        if not response:
            raise StorageError('{maak_bestand_uit_template} Aanmaken van bestand %s in folder %s is mislukt' % (
                                                                                                    repr(fname),
                                                                                                    repr(folder_name)))

        file_id = response['id']

        # geef iedereen toestemming om dit bestand te wijzigen
        request = self._service_perms.create(fileId=file_id,
                                             body={
                                                 "type": "anyone",
                                                 "role": "writer",
                                                 "allowFileDiscovery": "true",
                                             })
        _response = self._execute(request)
        # self.stdout.write('[DEBUG] {maak_bestand_uit_template} perms create result is %s' % repr(_response))

        return file_id

    def _save_bestand(self, afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, rayon_nr: int,
                      fname: str, file_id: str):

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        msg = '[%s] Aangemaakt\n' % stamp_str
        bestand, is_created = Bestand.objects.get_or_create(
                                    begin_jaar=self._begin_jaar,
                                    afstand=afstand,
                                    is_teams=is_teams,
                                    is_bk=is_bk,
                                    klasse_pk=klasse_pk,
                                    rayon_nr=rayon_nr,
                                    fname=fname,
                                    file_id=file_id)
        if is_created:
            bestand.log = msg
            bestand.save(update_fields=['log'])

    def maak_sheet_van_template(self, afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, rayon_nr: int, fname: str) -> str:
        """ maak een Google Sheet aan """

        error_msg = None
        tb_list = list()
        file_id = None

        try:
            if not self._service_files:
                self._setup_service()
                self._secure_folders()      # alle folders vinden of maken
                self._vind_templates()      # alle templates vinden

            folder_name = self._params_to_folder_name(afstand, is_teams, is_bk)
            file_id = self._vind_comp_bestand(folder_name, fname)
            if not file_id:
                # bestaat nog niet
                file_id = self._maak_bestand_uit_template(folder_name, fname)
            self._save_bestand(afstand, is_teams, is_bk, klasse_pk, rayon_nr, fname, file_id)

        except KeyError as exc:
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            error_msg = 'KeyError: %s' % exc

        except (IndexError, ValueError) as exc:     # pragma: no cover
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            error_msg = 'Exception: %s' % exc

        except socket.timeout as exc:               # pragma: no cover
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            error_msg = 'Socket timeout exception: %s' % exc

        except socket.gaierror as exc:              # pragma: no cover
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            # example: [Errno -3] Temporary failure in name resolution
            error_msg = 'Socket exception: %s' % exc

        except GoogleApiError as exc:
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            error_msg = 'GoogleApiError: %s' % exc.reason

        except RefreshError as exc:
            e_type, _, tb = sys.exc_info()
            tb_list = traceback.format_tb(tb)
            error_msg = 'RefreshError: %s' % exc

        if error_msg:
            msg = 'Onverwachte fout in storage_drive:\n'
            msg += '   %s\n' % error_msg
            if tb_list:                             # pragma: no branch
                msg += 'Traceback:\n'
                msg += ''.join(tb_list)
            raise StorageError('{google_drive} ' + msg)

        return file_id


# end of file
