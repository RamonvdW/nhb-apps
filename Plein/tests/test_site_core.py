# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from Site.core.background_sync import BackgroundSync
from Site.core.minify_js import AppJsMinifyFinder
import tempfile
import os


class TestSiteCore(TestCase):

    """ unit tests voor de Site applicatie, diverse core modules """

    def test_background_sync(self):
        sync = BackgroundSync(settings.BACKGROUND_SYNC_POORT)

        got_ping = sync.wait_for_ping(timeout=0.01)
        self.assertFalse(got_ping)

        sync.ping()

        got_ping = sync.wait_for_ping(timeout=0.01)
        self.assertTrue(got_ping)

    def test_conflict(self):
        sync1 = BackgroundSync(settings.BACKGROUND_SYNC_POORT)
        sync2 = BackgroundSync(settings.BACKGROUND_SYNC_POORT)

        got_ping = sync1.wait_for_ping(timeout=0.01)
        self.assertFalse(got_ping)

        # another received on the same port is not possible
        got_ping = sync2.wait_for_ping(timeout=0.01)
        self.assertFalse(got_ping)

    def test_minify_js(self):
        obj = AppJsMinifyFinder(app_names=['Avoid all real apps'])

        # add a fake app
        with tempfile.TemporaryDirectory() as tmp_dir:
            js_dir = os.path.join(tmp_dir, 'js')
            os.mkdir(js_dir)
            os.mkdir(os.path.join(js_dir, 'confusing.js'))
            os.mkdir(os.path.join(js_dir, 'real_subdir'))
            obj.apps_with_js['test'] = tmp_dir

            # make app dirs (these are normally made by AppJsMinifyFinder.__init__)
            os.mkdir(os.path.join(tmp_dir, 'static'))
            os.mkdir(os.path.join(tmp_dir, 'static', 'test_js_min'))

            with open(os.path.join(js_dir, 'unclosed_string.js'), 'w') as f:
                msg = "/* mandatory copyright */\n"
                msg += "function x() {\n"
                msg += "// eens kijken met zo'n quote\n"
                msg += "/* goed zo met quote' */\n"
                msg += "x = 'test \\'niet\\' meer'; /* jaja */\n"
                msg += "const data = \"dit gaat niet goed';\n"
                msg += "}\n"
                f.write(msg)

            with open(os.path.join(js_dir, 'eof_comment_1.js'), 'w') as f:
                msg = "/* mandatory copyright */\n"
                msg += "// quote' and missing newline"
                f.write(msg)

            with open(os.path.join(js_dir, 'eof_comment_2.js'), 'w') as f:
                msg = "/* mandatory copyright */\n"
                msg += "/* quote' and missing closure"
                f.write(msg)

            with open(os.path.join(js_dir, 'not_js.txt'), 'w') as f:
                f.write('hello world')

            # doe de minification
            for _ in obj.list():        # pragma: no branch
                pass                    # pragma: no cover

            # nog een keer, dan worden de directories niet aangemaakt
            for _ in obj.list():        # pragma: no branch
                pass                    # pragma: no cover

        obj.find('')


# end of file
