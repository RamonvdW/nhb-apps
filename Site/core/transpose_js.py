# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.conf import settings
from django.contrib.staticfiles.finders import BaseFinder
import os
import re


class AppJsFinder(BaseFinder):
    """ Invoked during collect static, if present in settings.STATICFILES_FINDERS """

    """
        Check each app for a "js" directory
        Read each app/js/xx.js file and save in app/static/app_js/xx.js, possibly transposing on the fly:
            - minify     (if settings.ENABLED_MINIFY == True)
            - instrument (if settings.ENABLED_INSTRUMENT_JS == True)

        Minify:
            Removes unnecessary spaces, newlines, comments.
            Keeps the copyright header.
            No obfuscation.

        Instrument:
            tbd
    """

    def __init__(self, app_names=None, *args, **kwargs):
        self.apps_with_js = dict()
        self.main = ''

        if settings.ENABLE_MINIFY and settings.ENABLE_INSTRUMENT_JS:
            raise SystemError('Conflicting settings: ENABLE_MINIFY and ENABLE_INSTRUMENT_JS')

        app_configs = apps.get_app_configs()
        if app_names:
            app_names = set(app_names)
            app_configs = [ac
                           for ac in app_configs
                           if ac.name in app_names]
        self._find_apps_with_js(app_configs)

        # maak meteen de static directories aan zodat deze gevonden kunnen worden door de AppDirectoriesFinder.__init__
        # (jammer dat het zoeken niet later gedaan wordt)
        self._make_static_dirs()

        if settings.ENABLE_INSTRUMENT_JS:
            # depends on 'coverage', which is not installed on prod
            from Site.js_cov.instrument_js import JsCovInstrument
            self._instrument_js = JsCovInstrument()

        super().__init__(*args, **kwargs)

    def _find_apps_with_js(self, app_configs):
        # note: this method is also invoked for each management command, so do very little work
        for app_config in app_configs:
            app_name = app_config.name
            js_dir = os.path.join(app_config.path, "js")
            if os.path.isdir(js_dir):
                self.apps_with_js[app_name] = app_config.path
        # for

    def _make_static_dirs(self):
        for app_name, app_path in self.apps_with_js.items():
            # zorg dat app/static/ bestaat
            static_dir = os.path.join(app_path, "static")
            if not os.path.isdir(static_dir):
                os.mkdir(static_dir)

            # zorg dat app/static/app_js/ bestaat
            js_min_dir = os.path.join(static_dir, "%s_js" % app_name.lower())
            if not os.path.isdir(js_min_dir):
                os.mkdir(js_min_dir)
        # for

    def list(self, ignore_patterns=None):
        # invoked to find static files
        # we use this to minify javascript files and create new static files on the fly
        for app_name, app_path in self.apps_with_js.items():
            # print('[DEBUG] Minify JS for app %s with app_path %s' % (app_name, app_path))
            dir_in = os.path.join(app_path, "js")
            dir_out = os.path.join(app_path, "static", "%s_js" % app_name.lower())
            self._list_dir_recursive(dir_in, dir_out, os.path.join(app_name, "js"))

            # fake yield to make this a generator function
            if dir_in == '':        # pragma: no cover
                yield
        # for

    def _list_dir_recursive(self, dir_in, dir_out, app_path):
        # minify elke file.js in dir_in
        # opslaan als dir_out/file.js
        for fname in os.listdir(dir_in):
            if fname.endswith('.js'):
                fpath_in = os.path.join(dir_in, fname)
                if os.path.isfile(fpath_in):
                    fpath_out = os.path.join(dir_out, fname)
                    self._transpose_js_file(fpath_in, fpath_out, os.path.join(app_path, fname))
            else:
                dir_in_sub = os.path.join(dir_in, fname)
                if os.path.isdir(dir_in_sub):
                    # subdirectories recursief afhandelen
                    self._list_dir_recursive(dir_in_sub, dir_out, app_path)
        # for

    def find(self, path, **kwargs):
        # niet nodig, wel verplicht
        return []

    def _transpose_js_file(self, fpath_in, fpath_out, app_path):
        """ put a copy of file fpath_in in fpath_out, possibly changing the contents on the fly:
            - minify
            - instrument
        """

        # print('[INFO] loading %s' % repr(app_path))
        with open(fpath_in, 'r') as f:
            contents = f.read()

        if settings.ENABLE_MINIFY:
            new_contents = self._minify_javascript(contents)

        elif settings.ENABLE_INSTRUMENT_JS:
            new_contents = self._instrument_js.instrument(contents, app_path)

        else:
            new_contents = contents

        # print('[INFO] Writing %s' % repr(fpath_out))
        with open(fpath_out, 'w') as f:
            f.write(new_contents)

    def _minify_javascript(self, script):
        """ Doorloop javascript en minify alles behalve strings (rudimentair!)
        """
        # keep the copyright header
        pos = script.find('*/\n')
        clean = script[:pos + 3]
        script = script[pos + 3:]

        while len(script):
            # zoek strings zodat we die niet wijzigen
            pos_dq = script.find('"')
            pos_sq = script.find("'")

            if pos_sq >= 0 and pos_dq >= 0:
                pos_q = min(pos_sq, pos_dq)  # both not -1 --> take first, thus min
            else:
                pos_q = max(pos_sq, pos_dq)  # either one is -1 --> take max, thus the positive one

            # zoek commentaar zodat we geen quotes in commentaar pakken /* can't */
            pos_sc = script.find('//')  # single line comment
            pos_bc = script.find('/*')  # block comment

            if pos_sc >= 0 and pos_bc >= 0:
                pos_c = min(pos_sc, pos_bc)  # both not -1 --> take first, thus min
            else:
                pos_c = max(pos_sc, pos_bc)  # either one is -1 --> take max, thus the positive one

            if pos_c >= 0 and pos_q >= 0:
                # zowel quote and commentaar
                if pos_c < pos_q:
                    # commentaar komt eerst

                    # verwerk het stuk script voordat het commentaar begint
                    pre_comment = script[:pos_c]
                    clean += self._minify_part(pre_comment)
                    script = script[pos_c:]

                    # verwijder het commentaar
                    if pos_c == pos_sc:
                        # verwijder single-line comment
                        pos = script.find('\n')
                        if pos > 0:
                            script = script[pos + 1:]
                        else:
                            script = ''
                    else:
                        # verwijder block comment
                        pos = script.find('*/')
                        if pos > 0:
                            script = script[pos + 2:]
                        else:
                            script = ''

                    # opnieuw evalueren
                    continue

            if pos_q >= 0:
                pre_string = script[:pos_q]
                clean += self._minify_part(pre_string)

                stop_char = script[pos_q]
                script = script[pos_q + 1:]  # kap pre-string en quote eraf
                pos = self._zoek_eind_quote(script, stop_char)
                clean += stop_char  # open char
                clean += script[:pos + 1]  # kopieer string inclusief stop-char

                script = script[pos + 1:]
            else:
                clean += self._minify_part(script)
                script = ''
        # while

        return clean

    @staticmethod
    def _minify_part(script):
        # remove block comments
        script = re.sub(r'/\*.*\*/', '', script)

        # remove single-line comments
        script = re.sub(r'//.*\n', '\n', script)

        # remove whitespace at start of the line
        script = re.sub(r'^\s+', '', script)
        script = re.sub(r'\n\s+', '\n', script)

        # remove newlines
        script = re.sub(r'\n', '', script)

        # remove whitespace around certain operators
        script = re.sub(r' = ', '=', script)
        script = re.sub(r' -= ', '-=', script)
        script = re.sub(r' \+= ', '+=', script)
        script = re.sub(r'\+ ', '+', script)
        script = re.sub(r' \+', '+', script)
        script = re.sub(r' \* ', '*', script)
        script = re.sub(r' :', ':', script)
        script = re.sub(r' == ', '==', script)
        script = re.sub(r' != ', '!=', script)
        script = re.sub(r' === ', '===', script)
        script = re.sub(r' !== ', '!==', script)
        script = re.sub(r' \+ ', '+', script)
        script = re.sub(r' - ', '-', script)
        script = re.sub(r' \? ', '?', script)
        script = re.sub(r' < ', '<', script)
        script = re.sub(r' > ', '>', script)
        script = re.sub(r' / ', '/', script)
        script = re.sub(r' && ', '&&', script)
        script = re.sub(r' \|\| ', '||', script)
        script = re.sub(r' >= ', '>=', script)
        script = re.sub(r' <= ', '<=', script)
        script = re.sub(r', ', ',', script)
        script = re.sub(r': ', ':', script)
        script = re.sub(r'; ', ';', script)
        script = re.sub(r'\) {', '){', script)
        script = re.sub(r'{ ', '{', script)
        script = re.sub(r' \(', '(', script)
        script = re.sub(r'} else', '}else', script)
        script = re.sub(r'else {', 'else{', script)
        script = re.sub(r' }', '}', script)

        # remove whitespace at end of the line
        script = re.sub(r'\s+\n', '\n', script)
        script = re.sub(r'\s+$', '', script)

        return script

    @staticmethod
    def _zoek_eind_quote(script, stop_char):
        start = pos = 0
        while start < len(script):                  # pragma: no branch (komt door de break)
            pos = script.find(stop_char, start)
            if pos > 0 and script[pos - 1] == '\\':
                # escaped, dus overslaan
                start = pos + 1
            else:
                break  # from the while
        # while
        return pos


# end of file
