# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van bestanden in een folder structuur in Google Drive """

from django.utils import timezone
from CompKamp.operations.wedstrijdformulieren import iter_wedstrijdformulieren
from GoogleDrive.models import Token, Bestand
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError as GoogleApiError
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from GoogleDrive.storage_base import Storage, StorageError
import socket
import json


class GoogleDriveStorage(Storage):

    """ let op: genereert StorageError exception """

    # Scopes that allow to edit, create, delete and share all of the owners' google drive files
    SCOPES = ['https://www.googleapis.com/auth/drive']

    # MIME types for items in a Google Driver folder
    MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'
    MIME_TYPE_SHEET = 'application/vnd.google-apps.spreadsheet'

    def __init__(self, stdout, begin_jaar: int, share_with_emails: list):
        super().__init__(stdout, begin_jaar, share_with_emails)

        self._creds = None
        self._service_files = None
        self._service_perms = None

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
        return self._creds.refresh_token

    def _setup_service(self):
        service = build("drive", "v3", credentials=self._creds)
        self._service_files = service.files()
        self._service_perms = service.permissions()

    def _maak_folder(self, parent_folder_id, folder_name):
        file_metadata = {
            "name": folder_name,
            "mimeType": self.MIME_TYPE_FOLDER,
            "parents": [parent_folder_id],
        }
        request = self._service_files.create(body=file_metadata, fields='id')   # fields is comma-separated

        results = request.execute()

        folder_id = results.get("id")
        return folder_id

    def _vind_globale_folder(self, folder_name):
        query = "mimeType='%s'" % self.MIME_TYPE_FOLDER
        query += " and trashed=false"
        query += " and name='%s'" % folder_name
        request = self._service_files.list(q=query)

        results = request.execute()

        if 'files' not in results:
            raise StorageError("{vind_globale_folder} Missing 'files' in results")

        # print('[DEBUG] {vind_globale_folder} results:', results)
        all_files = results['files']
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

        results = request.execute()

        if 'files' not in results:
            raise StorageError("{list_folder} Missing 'files' in results")

        # print('[DEBUG] list folder results:', results)
        out = {obj['name']: obj['id']
               for obj in results['files']}
        return out

    def _share_seizoen_folder(self):
        if self._folder_id_seizoen:
            # request = self._service_files.get(fileId=self._folder_id_seizoen)
            # response = request.execute()
            # print('{share_seizoen_folder} files.get response=%s' % repr(response))

            request = self._service_perms.list(fileId=self._folder_id_seizoen,
                                               fields="permissions(id, role, type, emailAddress)")

            response = request.execute()

            self.stdout.write('[INFO] {share_seizoen_folder} perms.list response=%s' % repr(response))
            share_with = self._share_with_emails[:]
            for perm in response['permissions']:
                if perm['type'] == 'user' and perm['emailAddress'] in share_with:
                    share_with.remove(perm['emailAddress'])
            # for

            for email in share_with:
                request = self._service_perms.create(fileId=self._folder_id_seizoen,
                                                     body={
                                                         "type": "user",
                                                         "role": "writer",
                                                         "emailAddress": email,
                                                     },
                                                     sendNotificationEmail=False)
                response = request.execute()
                self.stdout.write('[INFO] {share_seizoen_folder} perms.create response=%s' % repr(response))
            # for

    def _vind_comp_bestand(self, folder_name, fname) -> str:
        folder_id_comp = self._comp2folder_id.get(folder_name, None)
        if not folder_id_comp:
            raise StorageError('Folder %s niet gevonden' % repr(folder_name))

        query = "name='%s'" % fname
        query += " and '%s' in parents" % folder_id_comp
        query += " and mimeType='%s'" % self.MIME_TYPE_SHEET
        request = self._service_files.list(q=query)

        results = request.execute()

        # self.stdout.write('[DEBUG] {vind_comp_bestand} results: %s' % repr(results))
        all_files = results['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            return first_file['id']
        return ""

    def _maak_bestand_uit_template(self, folder_name, fname) -> str:
        # kopieer een template naar een nieuw bestand
        # print('[DEBUG] {google_drive.maak_bestand_uit_template} folder_name=%s, fname=%s' % (repr(folder_name),
        #                                                                                      repr(fname)))
        folder_id = self._comp2folder_id[folder_name]
        template_file_id = self._comp2template_file_id[folder_name]

        request = self._service_files.copy(fileId=template_file_id,
                                           body={"parents": [folder_id],
                                                 "name": fname})

        result = request.execute()

        # self.stdout.write('[DEBUG] {maak_bestand_uit_template} result is %s' % repr(result))
        file_id = result['id']
        return file_id

    def _save_bestand(self, afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, fname: str, file_id: str):
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        msg = '[%s] Aangemaakt\n' % stamp_str
        Bestand.objects.create(
                begin_jaar=self._begin_jaar,
                afstand=afstand,
                is_teams=is_teams,
                is_bk=is_bk,
                klasse_pk=klasse_pk,
                fname=fname,
                file_id=file_id,
                log=msg)

    def maak_sheet_van_template(self, afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, fname: str) -> str:
        """ maak een Google Sheet aan """

        # TODO: kijk in Bestand ?

        error_msg = None
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
                self._save_bestand(afstand, is_teams, is_bk, klasse_pk, fname, file_id)

        except KeyError as exc:
            error_msg = 'KeyError: %s' % exc

        except (IndexError, ValueError) as exc:     # pragma: no cover
            error_msg = 'Exception: %s' % exc

        except socket.timeout as exc:               # pragma: no cover
            error_msg = 'Socket timeout exception: %s' % exc

        except socket.gaierror as exc:              # pragma: no cover
            # example: [Errno -3] Temporary failure in name resolution
            error_msg = 'Socket exception: %s' % exc

        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason

        except RefreshError as exc:
            error_msg = 'RefreshError: %s' % exc

        if error_msg:
            raise StorageError('{google_drive} ' + error_msg)

        return file_id


def ontbrekende_wedstrijdformulieren_rk_bk(comp) -> list:
    """ geef een lijst terug met de benodigde wedstrijdformulieren die nog niet aangemaakt zijn
        aan de hand van de informatie in tabel Bestand.
    """
    todo = list()

    # maak een map met de huidige bestanden
    sel2bestand = dict()
    for bestand in Bestand.objects.filter(begin_jaar=comp.begin_jaar, afstand=comp.afstand):
        sel = (bestand.begin_jaar, bestand.afstand, bestand.is_teams, bestand.is_bk, bestand.klasse_pk)
        sel2bestand[sel] = bestand
    # for

    for tup in iter_wedstrijdformulieren(comp):
        afstand, is_teams, is_bk, klasse_pk, fname = tup
        sel = (comp.begin_jaar, afstand, is_teams, is_bk, klasse_pk)
        if sel not in sel2bestand:
            # niet gevonden; voeg toe aan de todo lijst
            todo.append(tup)
    # for

    return todo


# end of file
