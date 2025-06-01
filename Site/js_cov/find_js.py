# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.apps import apps
import os


class JsCovFind:
    """ Invoked from Plein.tests.test_js_in_browser, when all browser tests have been run
        and the coverage data is available """

    """ find javascript files, in order to have them in scope during execution, for js_cov to capture.
    """

    def __init__(self, data):
        self._js_files = list()

        # instead of only reporting the files that are in the coverage report,
        # process all application JS files
        for app_config in apps.get_app_configs():
            app_name = app_config.name
            js_dir = os.path.join(app_config.path, "js")
            if os.path.isdir(js_dir):
                for fname in os.listdir(js_dir):
                    if fname.endswith('.js'):
                        js_fname = os.path.join(js_dir, fname)
                        if os.path.isfile(js_fname):
                            js_fname_short = os.path.join(app_name, "js", fname)
                            if js_fname_short in data:
                                for range_start, range_end in self._make_ranges(data[js_fname_short]):
                                    self._found_js_cov(js_fname_short, range_start, range_end)
                                # for
                            else:
                                # report the filename, but no lines were covered
                                self._found_js_cov(js_fname_short, -1, -1)
                # for
        # for

    @staticmethod
    def _make_ranges(nrs):
        # convert a list of numbers, partially consecutive, into a list of ranges
        nrs.sort()
        ranges = list()
        i = 0
        while i < len(nrs):
            j = i + 1
            if j < len(nrs) and nrs[j] == nrs[i] + 1:
                # more than 1 number remaining and it is consecutive
                # try to extend even more
                while j + 1 < len(nrs) and nrs[j + 1] == nrs[j] + 1:
                    j += 1
                # while
                tup = (nrs[i], nrs[j])
                ranges.append(tup)
                i = j + 1
            else:
                # last number or single number range
                tup = (nrs[i], nrs[i])
                ranges.append(tup)
                i += 1
        # while
        return ranges

    def _found_js_cov(self, js_fname: str, range_start: int, range_end: int):
        """ special function that is used by js_cov to inject all JS filenames and executed ranges """
        self._js_files.append(js_fname)     # avoids optimization


# end of file
