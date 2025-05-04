# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
from django.contrib.staticfiles.finders import BaseFinder
import os
import re


class AppJsMinifyFinder(BaseFinder):
    """
        Check each app for a "js" directory
        Minify each app/js/xx.js file and save in app/static/app_js_min/xx_min.js

        Removes unnecessary spaces, newlines, comments.
        Keeps the copyright header.
        No obfuscation.
    """

    def __init__(self, app_names=None, *args, **kwargs):
        self.apps_with_js = dict()
        self.main = ''

        app_configs = apps.get_app_configs()
        if app_names:
            app_names = set(app_names)
            app_configs = [ac
                           for ac in app_configs
                           if ac.name in app_names]
        self._find_apps_with_js(app_configs)

        super().__init__(*args, **kwargs)

    def _find_apps_with_js(self, app_configs):
        # note: this method is also invoked for each management command, so do very little work
        for app_config in app_configs:
            app_name = app_config.name
            js_dir = os.path.join(app_config.path, "js")
            if os.path.isdir(js_dir):
                self.apps_with_js[app_name] = app_config.path
        # for

    def list(self, ignore_patterns=None):
        # invoked to find static files
        # we use this to minify javascript files and create new static files on the fly
        for app_name, app_path in self.apps_with_js.items():
            # print('[DEBUG] Minify JS for app %s' % app_name)
            js_dir = os.path.join(app_path, "js")

            # zorg dat app/static/ bestaat
            static_dir = os.path.join(app_path, "static")
            if not os.path.isdir(static_dir):
                os.mkdir(static_dir)

            # zorg dat app/static/app_js_min/ bestaat
            js_min_dir = os.path.join(app_path, "static", "%s_js_min" % app_name.lower())
            if not os.path.isdir(js_min_dir):
                os.mkdir(js_min_dir)

            self._list_dir_recursive(js_dir, js_min_dir)

            # fake yield to make this a generator function
            if js_dir == '':        # pragma: no cover
                yield
        # for

    def _list_dir_recursive(self, fpath, js_min_dir):
        # minify elke file.js
        # opslaan als file_min.js
        for fname in os.listdir(fpath):
            if fname.endswith('.js'):
                fname_min = fname[:-3] + '_min.js'
                fpath_in = os.path.join(fpath, fname)
                if os.path.isfile(fpath_in):
                    fpath_out = os.path.join(js_min_dir, fname_min)
                    self._minify_js_file(fpath_in, fpath_out)
            else:
                fpath_sub = os.path.join(fpath, fname)
                if os.path.isdir(fpath_sub):
                    # subdirectories recursief afhandelen
                    self._list_dir_recursive(fpath_sub, js_min_dir)
        # for

    def find(self, path, all=False):
        # niet nodig, wel verplicht
        return []

    def _minify_js_file(self, fpath_in, fpath_out):
        # print('[INFO] loading %s' % repr(fpath_in))
        with open(fpath_in, 'r') as f:
            contents = f.read()

        new_contents = self._minify_javascript(contents)

        # print('[INFO] writing %s' % repr(fpath_out))
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
                script = ""
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
