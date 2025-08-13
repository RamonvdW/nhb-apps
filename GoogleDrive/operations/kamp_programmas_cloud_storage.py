# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" aanmaken en vinden van RK/BK programma's in de vorm van Google Sheets
    in een folder structuur in een Google Storage bucket met behulp via een service account """

from google.oauth2.service_account import Credentials
from google.cloud import storage
from google.cloud import storage_control_v2
from googleapiclient.errors import HttpError as GoogleApiError
import socket


class StorageError(Exception):
    pass


class Storage:

    BUCKET_NAME = "mh-formulieren"

    SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write']

    # in de root, moet shared zijn met service account
    FOLDER_NAME_WEDSTRIJD_FORMULIEREN = 'mh-wedstrijd-formulieren'
    FOLDER_NAME_TEMPLATES = 'Google sheet templates'

    MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'     # a folder in Google Drive is a file with this MIME type
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

    def __init__(self, stdout, service_account_fpath: str, begin_jaar: int):
        self.stdout = stdout
        self._service_account_fpath = service_account_fpath
        self._seizoen = 'Bondscompetities %s/%s' % (begin_jaar, begin_jaar + 1)

        self._did_initialize = False
        self.storage_client = None
        self.storage_control_client = None
        self._bucket = None
        self._folders_root = ""
        self._folder_id_top = ""
        self._folder_id_seizoen = ""
        self._folder_id_templates = ""
        self._comp2folder_id = dict()           # ["Indoor Teams RK"] = folder_id
        self._comp2template_file_id = dict()    # ["Indoor Teams RK"] = file_id

    def _init_service(self):
        creds = Credentials.from_service_account_file(self._service_account_fpath,
                                                      scopes=self.SCOPES)
        self.storage_client = storage.Client(credentials=creds)
        self.bucket = storage.bucket.Bucket(name=self.BUCKET_NAME, client=self.storage_client)
        if not self.bucket.exists():
            raise StorageError('Cannot access bucket %s' % repr(self.BUCKET_NAME))

        # storage control client is needed for folder management
        self.storage_control_client = storage_control_v2.StorageControlClient(credentials=creds)
        self._folders_root = 'projects/_/buckets/%s/folders' % self.BUCKET_NAME

    def _vind_folder(self, folder_name, parent_folder_id=None):
        #folder_path = self.storage_control_client.managed_folder_path('_', self.BUCKET_NAME, folder_name)
        #print('managed_folder_path: %s' % folder_path)

        # bucket_path = "projects/_/buckets/mh-formulieren"
        # request = storage_control_v2.ListFoldersRequest(parent=bucket_path)
        # response = self.storage_control_client.list_folders(request)
        # print('response: %s' % repr(response))
        # krak

        #request = storage_control_v2.CreateFolderRequest(folder=folder_path)

        folder_path = '%s/%s' % (self._folders_root,self.FOLDER_NAME_WEDSTRIJD_FORMULIEREN)
        request = storage_control_v2.GetFolderRequest(name=folder_path)
        response = self.storage_control_client.get_folder(request=request)
        print('get_folder response: %s' % response)

        kreak

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

    # ISSUE: als je een folder aanmaakt in een google drive van iemand anders, dan wordt je owner
    #        maar een service account heeft 0 storage quota

    # def _maak_folder(self, folder_name, parent_folder_id):
    #     file_metadata = {
    #         "name": folder_name,
    #         "mimeType": "application/vnd.google-apps.folder",
    #         "parents": [parent_folder_id],
    #     }
    #     request = self._service_files.create(body=file_metadata)
    #
    #     error_msg = None
    #     try:
    #         results = request.execute()
    #     except GoogleApiError as exc:
    #         error_msg = 'GoogleApiError: %s' % exc.reason
    #         results = None
    #     if error_msg:
    #         raise StorageError('{maak_folder} ' + error_msg)
    #
    #     self.stdout.write('[DEBUG] maak folder results: %s' % repr(results))
    #     folder_id = results['id']
    #     return folder_id

    # def _vind_of_maak_folder(self, folder_name, parent_folder_id):
    #     # find or create a folder with the given name, in the give parent folder
    #     folder_id = self._vind_folder(folder_name, parent_folder_id)
    #     if not folder_id:
    #         folder_id = self._maak_folder(folder_name, parent_folder_id)
    #     return folder_id

    def _vind_top_folder(self):
        # find the top folder
        self._folder_id_top = self._vind_folder(self.FOLDER_NAME_WEDSTRIJD_FORMULIEREN)
        self.stdout.write('[INFO] Top folder id is %s' % repr(self._folder_id_top))

    def _vind_templates_folder(self):
        # find the templates folder inside the top folder
        self._folder_id_templates = self._vind_folder(self.FOLDER_NAME_TEMPLATES, self._folder_id_top)
        self.stdout.write('[INFO] Templates folder id is %s' % repr(self._folder_id_templates))

    def _vind_of_maak_seizoen_folder(self):
        # maak een folder "Bondscompetities 2024/2025"
        self._folder_id_seizoen = self._vind_folder(self._seizoen, self._folder_id_top)
        if not self._folder_id_seizoen:
            raise StorageError('Kan folder met naam %s niet vinden.' % self._seizoen)

    # def _vind_of_maak_competitie_folders(self):
    #     # maak folders voor het RK en BK voor elke competitie
    #     # naam van de folder: "<Indoor|25m1pijl> <Individueel|Teams> <RK|BK>"
    #     gevonden = self._list_folder(self._folder_id_seizoen, folders_only=True)
    #
    #     missing = list()
    #     for comp_name in self.COMP2TEMPLATE.keys():
    #         try:
    #             folder_id = gevonden[comp_name]
    #         except KeyError:
    #             # probeer aan te maken
    #             folder_id = self._maak_folder(comp_name, self._folder_id_seizoen)
    #             if not folder_id:
    #                 missing.append(comp_name)
    #         self._comp2folder_id[comp_name] = folder_id
    #     # for
    #
    #     if len(missing):
    #         raise StorageError('Folders niet gevonden voor competities %s' % ", ".join(missing))

    def _secure_folders(self):
        self._vind_top_folder()
        self._vind_templates_folder()
        self._vind_of_maak_seizoen_folder()
        # self._vind_of_maak_competitie_folders()

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

    def _vind_comp_bestand(self, folder_id, fname) -> str:
        query = "name='%s'" % fname
        query += " and '%s' in parents" % folder_id
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

        self.stdout.write('[DEBUG] {vind_comp_bestand} results: %s' % repr(results))
        all_files = results['files']
        if len(all_files) > 0:
            first_file = all_files[0]
            return first_file['id']
        return ""

    def _copy_template_to(self, template_file_id, folder_id, fname) -> str:
        # kopieer een template naar een nieuw bestand
        request = self._service_files.copy(fileId=template_file_id,
                                           body={"parents": [folder_id],
                                                 "title": fname})
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

    def vind_sheet(self, afstand: int, is_teams: bool, is_bk: bool, fname: str, mag_aanmaken=False):
        """ vind een Google Sheet aan """

        folder_name = self._params_to_folder_name(afstand, is_teams, is_bk)

        error_msg = None
        file_id = None

        try:
            if not self._did_initialize:
                self._init_service()            # verbinden
                self._secure_folders()          # alle folders vinden of maken
                self._vind_templates()          # alle templates vinden
                self._did_initialize = True

            folder_id = self._folder_id_seizoen  # self._comp2folder_id[folder_name]

            file_id = self._vind_comp_bestand(folder_id, fname)
            if not file_id:
                # bestaat nog niet
                template_file_id = self._comp2template_file_id[folder_name]
                file_id = self._copy_template_to(template_file_id, folder_id, fname)

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
