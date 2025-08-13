# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van RK/BK programma's in de vorm van Google Sheets in een folder structuur in Google Drive. """

from django.conf import settings
from GoogleDrive.models import Token
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError as GoogleApiError
from google.oauth2.credentials import Credentials
import socket
import json

#SERVICE_ACCOUNT_FILE = '/tmp/mh-wedstrijd-formulieren_service-account.json'
CLIENT_ID_AND_SECRET = '/tmp/mh_wedstrijdformulieren_oauth_client_id_and_secret.json'

class StorageError(Exception):
    pass


class Storage:

    SCOPES = ['https://www.googleapis.com/auth/drive']  # edit, create and delete all of your google drive files

    # in de root, moet shared zijn met service account
    FOLDER_NAME_WEDSTRIJD_FORMULIEREN = 'MH wedstrijdformulieren'       # let op: globaal uniek!
    FOLDER_NAME_TEMPLATES = 'MH templates RK/BK'

    # MIME types for items in a Google Driver folder
    MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'
    MIME_TYPE_SHEET = 'application/vnd.google-apps.spreadsheet'

    COMP2TEMPLATE = {
        # dezelfde template voor 25m1pijl indoor RK/BK
        '25m1pijl Individueel RK': 'template-25m1pijl-individueel',
        '25m1pijl Individueel BK': 'template-25m1pijl-individueel',

        # dezelfde template voor Indoor individueel RK/BK
        'Indoor Individueel RK': 'template-indoor-individueel',
        'Indoor Individueel BK': 'template-indoor-individueel',

        # dezelfde template voor alle team wedstrijden
        '25m1pijl Teams RK': 'template-teams',
        '25m1pijl Teams BK': 'template-teams',
        'Indoor Teams RK': 'template-teams',
        'Indoor Teams BK': 'template-teams',
    }

    def __init__(self, stdout, begin_jaar: int):
        self.stdout = stdout

        self._seizoen_str = 'Bondscompetities %s/%s' % (begin_jaar, begin_jaar + 1)
        self._folder_id_top = ""
        self._folder_id_templates = ""
        self._folder_id_seizoen = ""
        self._folder_id_indoor = ""
        self._folder_id_25m1pijl = ""
        self._comp2folder_id = dict()           # ["Indoor Teams RK"] = folder_id
        self._comp2template_file_id = dict()    # ["Indoor Teams RK"] = file_id

        try:
            self.token = Token.objects.first()
        except Token.DoesNotExist:
            raise StorageError('No token')

        js_data = json.loads(self.token.creds)
        self.creds = Credentials.from_authorized_user_info(js_data)

        self._service_files = None
        self._service_perms = None

    def _setup_service(self):
        service = build("drive", "v3", credentials=self.creds)
        self._service_files = service.files()
        self._service_perms = service.permissions()

    def check_access(self):
        # google api libs refresh the token automatically
        return self.creds.refresh_token

    @staticmethod
    def _params_to_folder_name(afstand: int, is_teams: bool, is_bk: bool) -> str:
        if afstand == 18:
            folder_name = "Indoor "
        elif afstand == 25:
            folder_name = "25m1pijl "
        else:
            raise StorageError('Geen valide afstand: %s' % repr(afstand))

        if is_teams:
            folder_name += "Teams "
        else:
            folder_name += "Individueel "

        if is_bk:
            folder_name += 'BK'
        else:
            folder_name += 'RK'

        return folder_name

    def _maak_folder(self, parent_folder_id, folder_name):
        file_metadata = {
            "name": folder_name,
            "mimeType": self.MIME_TYPE_FOLDER,
            "parents": [parent_folder_id],
        }
        request = self._service_files.create(body=file_metadata, fields='id')

        error_msg = None
        try:
            results = request.execute()
        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason
            results = None
        if error_msg:
            raise StorageError('{maak_folder} ' + error_msg)

        folder_id = results.get("id")
        return folder_id

    def _vind_folder(self, folder_name, parent_folder_id=None):
        query = "mimeType='%s'" % self.MIME_TYPE_FOLDER
        query += " and name='%s'" % folder_name
        if parent_folder_id:
            query += " and '%s' in parents" % parent_folder_id
        request = self._service_files.list(q=query)

        error_msg = None
        try:
            results = request.execute()
        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason
            results = None
        if error_msg:
            raise StorageError('{vind_folder} ' + error_msg)

        # print('[DEBUG] vind folder results:', results)
        all_files = results['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            folder_id = first_file['id']
        else:
            # niet gevonden
            folder_id = None
        return folder_id

    def _list_folder(self, parent_folder_id, folders_only=False):
        # haalt de inhoud van een folder op
        # retourneer een dictionary: ["name"] = id
        query = "'%s' in parents" % parent_folder_id
        if folders_only:
            query += " and mimeType='%s'" % self.MIME_TYPE_FOLDER
        request = self._service_files.list(q=query)

        error_msg = None
        try:
            results = request.execute()
        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason
            results = None
        if error_msg:
            raise StorageError('{list_folder} ' + error_msg)

        # print('[DEBUG] list folder results:', results)
        out = {obj['name']: obj['id']
               for obj in results['files']}
        return out

    def _vind_top_folder(self):
        # find the top folder
        self._folder_id_top = self._vind_folder(self.FOLDER_NAME_WEDSTRIJD_FORMULIEREN)
        self.stdout.write('[INFO] %s folder id is %s' % (repr(self.FOLDER_NAME_WEDSTRIJD_FORMULIEREN),
                                                         repr(self._folder_id_top)))

    def _vind_template_folder(self):
        # find the top folder
        self._folder_id_templates = self._vind_folder(self.FOLDER_NAME_TEMPLATES)
        self.stdout.write('[INFO] %s folder id is %s' % (repr(self.FOLDER_NAME_TEMPLATES),
                                                         repr(self._folder_id_templates)))

    def _vind_of_maak_folder(self, parent_folder_id, folder_name):
        folders = self._list_folder(parent_folder_id)
        try:
            folder_id = folders[folder_name]
        except KeyError:
            # niet gevonden --> aanmaken
            folder_id = self._maak_folder(parent_folder_id, folder_name)

        return folder_id

    def _vind_of_maak_seizoen_folder(self):
        if self._folder_id_top:
            self._folder_id_seizoen = self._vind_of_maak_folder(self._folder_id_top, self._seizoen_str)
            self.stdout.write('[INFO] %s folder id is %s' % (repr(self._seizoen_str), repr(self._folder_id_seizoen)))

    def _vind_of_maak_deel_folders(self):
        if self._folder_id_seizoen:
            for afstand in (18, 25):
                for is_teams in (True, False):
                    for is_bk in (True, False):
                        folder_name = self._params_to_folder_name(afstand, is_teams, is_bk)
                        folder_id_comp = self._vind_of_maak_folder(self._folder_id_seizoen, folder_name)
                        self._comp2folder_id[folder_name] = folder_id_comp
                        self.stdout.write('[INFO] %s folder id is %s' % (repr(folder_name), repr(folder_id_comp)))
                    # for
                # for
            # for

    def _share_seizoen_folder(self, share_with_emails: list):
        if self._folder_id_seizoen:
            pass

        # request = self._service_files.get(fileId=self._folder_id_seizoen)
        # response = request.execute()
        # print('{share_seizoen_folder} files.get response=%s' % repr(response))

        request = self._service_perms.list(fileId=self._folder_id_seizoen,
                                           fields="permissions(id, role, type, emailAddress)")
        response = request.execute()
        self.stdout.write('[INFO] {share_seizoen_folder} perms.list response=%s' % repr(response))

        share_with = share_with_emails[:]
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

    def _secure_folders(self):
        self._vind_top_folder()                 # MH wedstrijdformulieren
        self._vind_template_folder()            # MH templates RK/BK
        self._vind_of_maak_seizoen_folder()     # Bondscompetities 2025/2026

        share_with = [
            'mh-support@handboogsport.nl',
            'mh-wedstrijd-formulieren@tensile-pixel-259816.iam.gserviceaccount.com',
        ]

        self._share_seizoen_folder(share_with)
        self._vind_of_maak_deel_folders()       # Indoor Teams RK etc.

    def _vind_templates(self):
        gevonden = self._list_folder(self._folder_id_templates)
        # print('[DEBUG] vind templates results:', gevonden)
        for found_name, found_id in gevonden.items():
            for key, name in self.COMP2TEMPLATE.items():
                if name == found_name:
                    self._comp2template_file_id[key] = found_id
            # for
        # for
        # print('self.comp2file_id: %s' % repr(self.comp2file_id))

        # controleer dat we alles hebben
        bad = False
        for key in self.COMP2TEMPLATE.keys():
            if key not in self._comp2template_file_id:
                self.stdout.write(
                    '[ERROR] Kan template %s niet vinden' % repr(self.COMP2TEMPLATE[key]))
                bad = True
        # for
        if bad:
            raise StorageError('Could not find all templates')

    def _vind_comp_bestand(self, folder_name, fname) -> str:
        folder_id_comp = self._comp2folder_id[folder_name]
        if not folder_id_comp:
            raise StorageError('Folder %s niet gevonden' % repr(folder_name))

        query = "name='%s'" % fname
        query += " and '%s' in parents" % folder_id_comp
        query += " and mimeType='%s'" % self.MIME_TYPE_SHEET
        request = self._service_files.list(q=query)

        error_msg = None
        try:
            results = request.execute()
        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason
            results = None
        if error_msg:
            raise StorageError('{vind_comp_bestand} ' + error_msg)

        # self.stdout.write('[DEBUG] {vind_comp_bestand} results: %s' % repr(results))
        all_files = results['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            return first_file['id']
        return ""

    def _maak_bestand_uit_template(self, folder_name, fname) -> str:
        # kopieer een template naar een nieuw bestand

        folder_id = self._comp2folder_id[folder_name]
        template_file_id = self._comp2template_file_id[folder_name]

        request = self._service_files.copy(fileId=template_file_id,
                                           body={"parents": [folder_id],
                                                 "name": fname})
        error_msg = None
        try:
            result = request.execute()
        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc.reason
            result = None
        if error_msg:
            raise StorageError('{copy_template_to} ' + error_msg)

        self.stdout.write('{copy_template_to} result is %s' % repr(result))
        file_id = result['id']
        return file_id

    def vind_sheet(self, afstand: int, is_teams: bool, is_bk: bool, fname: str, mag_aanmaken=False):
        """ vind een Google Sheet aan """

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
                if mag_aanmaken:
                    file_id = self._maak_bestand_uit_template(folder_name, fname)

        except (IndexError, KeyError, ValueError) as exc:
            error_msg = '[ERROR] Service error: %s' % exc

        except socket.timeout as exc:
            error_msg = 'Socket timeout exception: %s' % exc

        except socket.gaierror as exc:
            # example: [Errno -3] Temporary failure in name resolution
            error_msg = 'Socket exception: %s' % exc

        except GoogleApiError as exc:
            error_msg = 'GoogleApiError: %s' % exc

        if error_msg:
            raise StorageError('{vind_sheet} ' + error_msg)

        return file_id


# end of file
