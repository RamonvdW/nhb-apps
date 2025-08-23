# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" template class """

class StorageError(Exception):
    pass


class Storage:

    # folder structuur:
    #   - top                           (FOLDER_NAME_TOP)
    #      +-- site                     (live/test/dev)
    #           +-- seizoen             (self._seizoen_str)
    #                +--- kampioenschap (bepaald door _params_to_folder_name)

    FOLDER_NAME_TEMPLATES = 'templates'     # moet uniek zijn in de drive
    FOLDER_NAME_TOP = 'top'                 # moet uniek zijn in de drive
    FOLDER_NAME_SITE = 'site'

    COMP2TEMPLATE = {
        'comp': 'template-name',
    }

    def __init__(self, stdout, begin_jaar: int, share_with_emails: list):
        self.stdout = stdout

        self._seizoen_str = 'Bondscompetities %s/%s' % (begin_jaar, begin_jaar + 1)
        self._begin_jaar = begin_jaar
        self._share_with_emails = share_with_emails

        self._folder_id_top = ""
        self._folder_id_templates = ""
        self._folder_id_site = ""
        self._folder_id_seizoen = ""

        self._comp2folder_id = dict()           # ["Indoor Teams RK"] = folder_id
        self._comp2template_file_id = dict()    # ["Indoor Teams RK"] = file_id

    @staticmethod
    def _params_to_folder_name(afstand: int, is_teams: bool, is_bk: bool) -> str:
        return "%s %s %s" % (afstand,
                             {True:"Teams", False:"Indiv"}[is_teams],
                             {True:"BK", False:"RK"}[is_bk])

    def check_access(self):
        # controleer dat de credentials nog bruikbaar zijn
        return self._seizoen_str != ''

    def _maak_folder(self, parent_folder_id, folder_name) -> str:
        folder_id = parent_folder_id + folder_name + '/'
        return folder_id

    def _vind_globale_folder(self, folder_name):
        folder_id = self._folder_id_top + folder_name + '/'
        return folder_id

    def _list_folder(self, parent_folder_id, folders_only=False):
        out = {parent_folder_id: str(folders_only),
               'template-name': 'template_file_id'}
        return out

    def _vind_of_maak_folder(self, parent_folder_id, folder_name):
        folders = self._list_folder(parent_folder_id, folders_only=True)
        try:
            folder_id = folders[folder_name]
        except KeyError:
            # niet gevonden --> aanmaken
            folder_id = self._maak_folder(parent_folder_id, folder_name)

        return folder_id

    def _vind_top_folder(self):
        # vind the globale root/top folder
        self._folder_id_top = self._vind_globale_folder(self.FOLDER_NAME_TOP)
        if not self._folder_id_top:
            raise StorageError('{vind_top_folder} Top folder %s not found' % repr(self.FOLDER_NAME_TOP))

        self.stdout.write('[INFO] %s folder id is %s' % (repr(self.FOLDER_NAME_TOP),
                                                         repr(self._folder_id_top)))

    def _vind_templates_folder(self):
        # vind de globale folder met de templates
        self._folder_id_templates = self._vind_globale_folder(self.FOLDER_NAME_TEMPLATES)
        if not self._folder_id_templates:
            raise StorageError('{vind_templates_folder} Templates folder %s not found' % repr(self.FOLDER_NAME_TEMPLATES))

        self.stdout.write('[INFO] %s folder id is %s' % (repr(self.FOLDER_NAME_TEMPLATES),
                                                         repr(self._folder_id_templates)))

    def _vind_of_maak_site_folder(self):
        if self._folder_id_top:     # pragma: no branch
            self._folder_id_site = self._vind_of_maak_folder(self._folder_id_top, self.FOLDER_NAME_SITE)
            self.stdout.write('[INFO] site folder id is %s' % repr(self._folder_id_site))

    def _vind_of_maak_seizoen_folder(self):
        if self._folder_id_site:     # pragma: no branch
            self._folder_id_seizoen = self._vind_of_maak_folder(self._folder_id_site, self._seizoen_str)
            self.stdout.write('[INFO] seizoen folder id is %s' % repr(self._folder_id_seizoen))

    def _vind_of_maak_deel_folders(self):
        if self._folder_id_seizoen:     # pragma: no branch
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

    def _share_seizoen_folder(self):
        if self._folder_id_seizoen:     # pragma: no branch
            self._folder_id_templates = self._share_with_emails[0]

    def _secure_folders(self):
        if not self._folder_id_top:
            self._vind_top_folder()                 # "MH wedstrijdformulieren"
            self._vind_templates_folder()            # "MH templates RK/BK"
            self._vind_of_maak_site_folder()        # "MijnHandboogsport (dev)"
            self._vind_of_maak_seizoen_folder()     # "Bondscompetities 2025/2026"
            self._share_seizoen_folder()
            self._vind_of_maak_deel_folders()       # "Indoor Teams RK etc."

    def _vind_templates(self):
        gevonden = self._list_folder(self._folder_id_templates)
        for found_name, found_id in gevonden.items():
            for key, name in self.COMP2TEMPLATE.items():
                if name == found_name:
                    self._comp2template_file_id[key] = found_id
            # for
        # for

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
        folder_id_comp = self._comp2folder_id.get(folder_name, '')
        if not folder_id_comp:
            raise StorageError('Folder %s niet gevonden' % repr(folder_name))

        file_id = folder_name + fname
        return file_id

    def _maak_bestand_uit_template(self, folder_name, fname) -> str:
        # kopieer een template naar een nieuw bestand
        folder_id = self._comp2folder_id[folder_name]
        template_file_id = self._comp2template_file_id[folder_name]
        file_id = folder_id + template_file_id + 'copy'
        return file_id

    def maak_sheet_van_template(self, afstand: int, is_teams: bool, is_bk: bool, klasse_pk: int, fname: str) -> str:
        """ maak een Google Sheet aan """

        self._secure_folders()      # alle folders vinden of maken
        self._vind_templates()      # alle templates vinden

        folder_name = self._params_to_folder_name(afstand, is_teams, is_bk)
        file_id = self._vind_comp_bestand(folder_name, fname)
        if not file_id:
            # bestaat nog niet
            file_id = self._maak_bestand_uit_template(folder_name, fname)

        return file_id


# end of file
