# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from Competitie.models import Competitie
from GoogleDrive.models import Token, Bestand
from GoogleDrive.operations.google_drive import (GoogleDriveStorage, StorageError,
                                                 ontbrekende_wedstrijdformulieren_rk_bk)
from TestHelpers.e2ehelpers import E2EHelpers
from googleapiclient.errors import HttpError as GoogleApiError
from httplib2 import Response
from unittest.mock import patch
import io


class GoogleApiFilesMock:

    def __init__(self, mode_str: str):
        self.mode_str = mode_str
        self.next_resp = {}

    def list(self, q:str):
        print('files.list (q=%s)' % repr(q))

        files = list()

        # q="mimeType='application/vnd.google-apps.folder' and name='forms'"
        if "name='top'" in q:
            folder = {'id': 'top_folder_id'}
            files.append(folder)

        if "name='templates'" in q:
            folder = {'id': 'templates_folder_id'}
            files.append(folder)

        if q == "'templates_folder_id' in parents":
            file = {'id': 'file101', 'name': 'template-name'}
            files.append(file)

        if q == "'top_folder_id' in parents":
            file = {'id': 'file1234', 'name': 'file1234'}
            files.append(file)

        if 'mimeType' in q and 'spreadsheet' in q:
            if self.mode_str != 'no files':
                file = {'id': 'file99', 'name': 'sheet99'}
                files.append(file)

        self.next_resp = {'files': files}

        return self

    def create(self, body: dict, fields: str):
        if self.mode_str == 'create_folder_error':
            self.next_resp = {'GoogleApiError': 'failed to create folder'}
        else:
            self.next_resp = {'id': 'new1234'}
        return self

    def copy(self, fileId: str, body: dict):
        # fileId=template_file_id,
        # body={"parents": [folder_id],
        #       "name": fname}
        self.next_resp = {'id': 'copy101'}
        return self

    def execute(self):
        resp = self.next_resp
        self.next_resp = {}

        if 'GoogleApiError' in resp:
            http_resp = Response(info={'status': 400})
            http_resp.reason = resp['GoogleApiError']
            raise GoogleApiError(resp=http_resp, content=b'duh')

        return resp


class GoogleApiPermsMock:

    def __init__(self, mode_str:str=''):
        self.mode_str = mode_str
        self.next_resp = {}

    def list(self, fileId, fields):
        self.next_resp = {'permissions': [{'id': 'perm1234', 'role': 'owner', 'type': 'hi', 'emailAddress': 'hi'}]}
        return self

    def create(self, fileId, body, sendNotificationEmail=True):
        self.next_resp = {}
        return self

    def execute(self):
        resp = self.next_resp
        self.next_resp = {}
        return resp


class GoogleApiMock:

    def __init__(self, mode_str:str=''):
        self.mode_str = mode_str

    def files(self):
        return GoogleApiFilesMock(self.mode_str)

    def permissions(self):
        return GoogleApiPermsMock(self.mode_str)


class TestGoogleDriveGoogleDrive(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module google_drive """

    def test_all(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        drive = GoogleDriveStorage(out, 2025, share_with_emails)

        with self.assertRaises(StorageError) as exc:
            drive.check_access()
        self.assertEqual(str(exc.exception), 'No token')

        Token.objects.create(creds='{"test": "nja"}')
        with self.assertRaises(StorageError) as exc:
            drive.check_access()
        self.assertTrue(str(exc.exception).startswith('Invalid credentials:'))

        Token.objects.create(creds='{"client_secret": "123", "refresh_token": "1234", "client_id": "1234"}')
        drive.check_access()

        # eerste aanroep, bestand bestaat nog niet
        self.assertEqual(Bestand.objects.count(), 0)
        my_service = GoogleApiMock('no files')
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            drive._comp2template_file_id[drive._params_to_folder_name(18, False, False)] = 'template101'
            drive.maak_sheet_van_template(18, False, False, 1, 'fname')

        self.assertEqual(Bestand.objects.count(), 1)
        bestand = Bestand.objects.first()
        self.assertEqual(bestand.begin_jaar, 2025)
        self.assertEqual(bestand.afstand, 18)
        self.assertFalse(bestand.is_teams)
        self.assertFalse(bestand.is_bk)
        self.assertTrue(str(bestand) != '')

        del drive
        drive = GoogleDriveStorage(out, 2025, share_with_emails)

        # bestand bestaat al wel
        my_service = GoogleApiMock()
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            # eerste aanroep
            drive.maak_sheet_van_template(18, False, False, 1, 'fname')

        del drive
        drive = GoogleDriveStorage(out, 2025, share_with_emails)

        # trigger an error during maak_folder
        my_service = GoogleApiMock('create_folder_error')
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            with self.assertRaises(StorageError) as exc:
                # create folder error
                drive.maak_sheet_van_template(18, False, False, 1, 'fname')
            self.assertEqual(str(exc.exception),
                             '{maak_folder} GoogleApiError: failed to create folder')

        print(out.getvalue())
        return

        folder_name = '42 False False'      # bedacht door storage_template._params_to_folder_name
        folder_id = '42FF_1234'
        drive._comp2folder_id[folder_name] = folder_id

        with self.assertRaises(StorageError):
            drive.maak_sheet_van_template(42, False, False, 1, 'fname')
        return
        with self.assertRaises(StorageError):
            with patch.object(drive, "_service_files", ServiceFiles()):
                drive.maak_sheet_van_template(42, False, False, 1, 'fname')

    def test_ontbrekende(self):
        comp = Competitie.objects.create(begin_jaar=2025, afstand='42')

        lst = ontbrekende_wedstrijdformulieren_rk_bk(comp)
        self.assertEqual(lst, [])

        Bestand.objects.create(
                    begin_jaar=comp.begin_jaar,
                    afstand=int(comp.afstand))

        tup = (42, False, False, 1, 'fname')
        with patch('GoogleDrive.operations.google_drive.iter_wedstrijdformulieren', return_value=[tup]):
            lst = ontbrekende_wedstrijdformulieren_rk_bk(comp)
            self.assertEqual(lst, [tup])


# end of file
