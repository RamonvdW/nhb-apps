# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.core.management.base import OutputWrapper
from Competitie.models import Competitie
from GoogleDrive.models import Token, Bestand
from GoogleDrive.operations.storage_drive import (StorageGoogleDrive, StorageError,
                                                  ontbrekende_wedstrijdformulieren_rk_bk)
from TestHelpers.e2ehelpers import E2EHelpers
from googleapiclient.errors import HttpError as GoogleApiError
from google.auth.exceptions import RefreshError
from httplib2 import Response
from unittest.mock import patch
import io


class GoogleApiFilesMock:

    def __init__(self, verbose):
        self.verbose = verbose
        self.next_resp = {}
        self.next_error = None
        self.file_nr = 100
        self.folder_nr = 200
        self.list_resp = dict()   # [q] = resp

        # vind globale top folder
        self.list_resp["mimeType='application/vnd.google-apps.folder' and trashed=false and name='top'"] = {
            'files': [
                {'id': 'top_folder_id', 'name': 'top folder'}
            ]
        }

        # vind globale templates folder
        self.list_resp["mimeType='application/vnd.google-apps.folder' and trashed=false and name='templates'"] = {
            'files': [
                {'id': 'templates_folder_id', 'name': 'templates'}
            ]
        }

        # inhoud van de top folder
        self.list_resp["'top_folder_id' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"] = {
            'files': [
                {'id': 'site1234', 'name': 'site'}
            ]
        }

        # templates
        self.list_resp["'templates_folder_id' in parents and trashed=false"] = {
            'files': [
                {'id': 'templ1', 'name': 'template-name'},
            ]
        }

        # inhoud van de site folder
        self.list_resp["'site1234' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'"] = {
            'files': [
                # geen files
            ]
        }

        self.list_resp["mimeType='application/vnd.google-apps.folder' and trashed=false and name='site1234'"] = {
            'files': [
                # geen files
            ]
        }

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.next_error = (error_str, match, error_type)

    def list(self, q:str):
        if self.verbose:        # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.list} files.list (q=%s)' % repr(q))

        try:
            self.next_resp = self.list_resp[q]
        except KeyError:
            if self.verbose:    # pragma: no cover
                print('[DEBUG] no standard response')
            self.next_resp = {'files': []}

        return self

    def create(self, body: dict, **kwargs):
        # kan alleen folders maken
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.create} body=%s, kwargs=%s' % (repr(body), repr(kwargs)))

        new_id = 'folder%s' % self.folder_nr
        self.folder_nr += 1
        self.next_resp = {'id': new_id, 'name': body['name']}

        # new empty folder
        q = "'%s' in parents and trashed=false and mimeType='application/vnd.google-apps.folder'" % new_id
        self.list_resp[q] = {'files': []}

        # add the folder to the parent
        parent_id = body['parents'][0]
        q = "'%s' in parents and trashed=false and mimeType='application/vnd.google-apps.spreadsheet'" % parent_id
        if q not in self.list_resp:
            self.list_resp[q] = {'files': []}
        self.list_resp[q]['files'].append(self.next_resp)

        return self

    def copy(self, body: dict, **kwargs):
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.copy} body=%s, kwargs=%s' % (repr(body), repr(kwargs)))

        new_id = 'copy%s' % self.file_nr
        name = body['name']
        self.file_nr += 1
        self.next_resp = {'id': new_id, 'name': name}

        # add the file/folder to the parent
        parent_id = body['parents'][0]
        q = "name='%s' and '%s' in parents and mimeType='application/vnd.google-apps.spreadsheet'" % (name, parent_id)
        self.list_resp[q] = {'files': []}
        self.list_resp[q]['files'].append(self.next_resp)

        return self

    def execute(self):
        resp = self.next_resp

        if self.next_error is not None:
            do_error = False
            error_msg, match, error_type = self.next_error
            for k, v in self.next_resp.items():
                if isinstance(v, list):
                    for d in v:
                        for k2, v2 in d.items():
                            if match in v2:
                                do_error = True
                        # for
                else:
                    if match in v:
                        do_error = True
            # for

            if do_error:
                if error_type == 'GoogleApiError':
                    if self.verbose:    # pragma: no cover
                        print('[DEBUG] {GoogleApiFilesMock.execute} Generating GoogleApiError (reason=%s)' % repr(error_msg))
                    http_resp = Response(info={'status': 400})
                    http_resp.reason = error_msg
                    self.next_error = None
                    raise GoogleApiError(resp=http_resp, content=b'duh')

                elif error_type == 'RefreshError':
                    if self.verbose:    # pragma: no cover
                        print('[DEBUG] {GoogleApiFilesMock.execute} Generating RefreshError (reason=%s)' % repr(error_msg))
                    raise RefreshError(error_msg)

                elif error_type == 'no files':
                    resp = {}

                elif error_type == 'empty folder':      # pragma: no branch
                    resp['files'] = []

                else:       # pragma: no cover
                    print('[DEBUG] {GoogleApiFilesMock.execute} Unknown error_type %s' % repr(error_type))

        self.next_resp = {}
        if self.verbose:    # pragma: no cover
            print('[DEBUG] {GoogleApiFilesMock.execute} returning %s' % repr(resp))
        return resp


class GoogleApiPermsMock:

    def __init__(self, verbose):
        self.verbose = verbose
        self.next_resp = {}
        self.next_error = None

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.next_error = (error_str, match, error_type)

    def list(self, **_kwargs):
        self.next_resp = {
            'permissions': [
                {'id': 'perm1234', 'role': 'owner', 'type': 'user', 'emailAddress': 'al-aanwezig@test.not'}
            ]}
        return self

    def create(self, **_kwargs):
        self.next_resp = {}
        return self

    def execute(self):
        resp = self.next_resp
        self.next_resp = {}
        return resp


class GoogleApiMock:

    def __init__(self, verbose=False):
        self.files_service = GoogleApiFilesMock(verbose)
        self.perms_service = GoogleApiPermsMock(verbose)

    def prime_error(self, error_str: str, match: str, error_type: str):
        self.files_service.prime_error(error_str, match, error_type)
        self.perms_service.prime_error(error_str, match, error_type)

    def files(self):
        return self.files_service

    def permissions(self):
        return self.perms_service


class TestGoogleDriveGoogleDrive(E2EHelpers, TestCase):

    """ tests voor de GoogleDrive applicatie, module google_drive """

    def test_check_access(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        drive = StorageGoogleDrive(out, 2025, share_with_emails)

        with self.assertRaises(StorageError) as exc:
            drive.check_access()
        self.assertEqual(str(exc.exception), 'No token')

        Token.objects.create(creds='{"test": "nja"}')
        with self.assertRaises(StorageError) as exc:
            drive.check_access()
        self.assertTrue(str(exc.exception).startswith('Invalid credentials:'))

        Token.objects.create(creds='{"client_secret": "123", "refresh_token": "1234", "client_id": "1234"}')
        drive.check_access()    # no exception

    def test_copy(self):
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']
        drive = StorageGoogleDrive(out, 2025, share_with_emails)

        folder_18_indiv_rk = drive._params_to_folder_name(18, False, False)

        # eerste aanroep, bestand bestaat nog niet
        self.assertEqual(Bestand.objects.count(), 0)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            drive._comp2template_file_id[folder_18_indiv_rk] = 'templ1'
            file_id = drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname1')
            self.assertEqual(file_id, 'copy100')

        self.assertEqual(Bestand.objects.count(), 1)
        bestand = Bestand.objects.first()
        self.assertEqual(bestand.begin_jaar, 2025)
        self.assertEqual(bestand.afstand, 18)
        self.assertFalse(bestand.is_teams)
        self.assertFalse(bestand.is_bk)
        self.assertTrue(str(bestand) != '')

        # tweede aanroep; service is al geïnitialiseerd, file bestaat op
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            file_id = drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname1')
            self.assertEqual(file_id, 'copy100')
        self.assertEqual(Bestand.objects.count(), 1)

    def test_vind_globale_folder(self):
        # fouten tijdens vind_globale_folder
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']

        # GoogleApiError
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            my_service.prime_error('test A', 'top', 'GoogleApiError')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual('{google_drive} GoogleApiError: test A',
                             str(exc.exception))
        del drive

        # RefreshError
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            my_service.prime_error('test B', 'top', 'RefreshError')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual("{google_drive} RefreshError: test B",
                             str(exc.exception))
        del drive

        # geen 'files' in response
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            my_service.prime_error('test C', 'top', 'no files')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual("{vind_globale_folder} Missing 'files' in results",
                             str(exc.exception))
        del drive

        # kan globale 'templates' folder niet vinden
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            my_service.prime_error('test D', 'templates', 'empty folder')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual("{vind_templates_folder} Templates folder 'templates' not found",
                             str(exc.exception))
        del drive

    def test_maak_folder(self):
        # fouten tijdens maak_folder
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']

        # GoogleApiError
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            my_service.prime_error('test F', 'folder204', 'GoogleApiError')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname')
            self.assertEqual('{google_drive} GoogleApiError: test F',
                             str(exc.exception))
        del drive

    def test_list_folder(self):
        # fouten tijdens list_folder
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not']

        # trigger GoogleApiError tijdens list_folder
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        folder_18_indiv_rk = drive._params_to_folder_name(18, False, False)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            drive._comp2template_file_id[folder_18_indiv_rk] = 'templ1'
            my_service.prime_error('test L1', 'site1234', 'GoogleApiError')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname3')
            self.assertEqual('{google_drive} GoogleApiError: test L1',
                             str(exc.exception))
        del drive

        # trigger de "no files" fout tijdens list_folder
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            drive._comp2template_file_id[folder_18_indiv_rk] = 'templ1'
            my_service.prime_error('test L2', 'site1234', 'no files')
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname3')
            self.assertEqual("{list_folder} Missing 'files' in results",
                             str(exc.exception))
        del drive

        # trigger de KeyError fout tijdens list_folder
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            with self.assertRaises(StorageError) as exc:
                drive.maak_sheet_van_template(18, False, False, 1, 3, 'fname3')
            self.assertEqual("{google_drive} KeyError: '18 Indiv RK'",
                             str(exc.exception))

    def test_share_seizoen(self):
        # speciale situaties tijdens share_seizoen_folder
        out = OutputWrapper(io.StringIO())
        share_with_emails = ['mgr@test.not', 'al-aanwezig@test.not']

        # voorkom dat de folder seizoen gevonden wordt
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            with patch.object(drive, '_vind_of_maak_seizoen_folder', return_value=''):
                # omdat de seizoen folder er niet is, zijn de deel-folders er ook niet
                with self.assertRaises(StorageError) as exc:
                    drive.maak_sheet_van_template(18, False, False, 1, 2, 'fname3')
                self.assertEqual("Folder '18 Indiv RK' niet gevonden",
                                 str(exc.exception))
        del drive

        # seizoen folder is al gedeeld
        drive = StorageGoogleDrive(out, 2025, share_with_emails)
        folder_18_indiv_rk = drive._params_to_folder_name(18, False, False)
        my_service = GoogleApiMock(verbose=False)
        with patch('GoogleDrive.operations.google_drive.build', return_value=my_service):
            drive._comp2template_file_id[folder_18_indiv_rk] = 'templ1'
            drive.maak_sheet_van_template(18, False, False, 1, 2, 'fname3')

    @staticmethod
    def _iter_wedstrijdformulieren(arg):
        yield 42, False, False, 1, 'fname1'
        yield 42, True, False, 1, 'fname2'

    def test_ontbrekende(self):
        comp = Competitie.objects.create(begin_jaar=2025, afstand='42')

        lst = ontbrekende_wedstrijdformulieren_rk_bk(comp)
        self.assertEqual(lst, [])

        Bestand.objects.create(
                    begin_jaar=comp.begin_jaar,
                    afstand=int(comp.afstand),
                    klasse_pk=1)

        with patch('GoogleDrive.operations.google_drive.iter_wedstrijdformulieren',
                   side_effect=self._iter_wedstrijdformulieren):
            lst = ontbrekende_wedstrijdformulieren_rk_bk(comp)
            #self.assertEqual(lst, [])


# end of file
