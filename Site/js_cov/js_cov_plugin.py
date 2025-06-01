# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Site.js_cov.instrument_js import JsCovInstrument
from coverage.misc import NoSource
import coverage.plugin
import json


class JsCoveragePluginException(Exception):
    """ Used for any errors from the plugin itself. """
    pass


class JsCoveragePlugin(coverage.plugin.CoveragePlugin, coverage.plugin.FileTracer):

    """ This class helps during 'coverage run' to pass the executed JS line numbers """

    def __init__(self, options):
        self.top_path = None
        self.js_cov_data = dict()       # [fname] = [1,2,3, ..] (lines executed)
        self._load_js_cov_data()

    def _load_js_cov_data(self):
        with open('/tmp/browser_js_cov.json', 'r') as f:
            data = f.read()
        self.js_cov_data = json.loads(data)
        # for k, v in self.js_cov_data.items():
        #     print("{js_cov} loaded: %s = %s" % (repr(k), repr(v)))

    def file_tracer(self, filename):
        # the trick is to find part of the python program that handles all JS files
        if filename.endswith('/Site/js_cov/find_js.py'):
            # print('{js_cov} file_tracer for %s' % repr(filename))
            self.top_path = filename[:-len('Site/js_cov/find_js.py')]
            # print('{js_cov} top_path=%s' % repr(self.top_path))
            return self

        # if filename.endswith('.js'):
        #     print('{js_cov} file_tracer for %s' % repr(filename))
        #     return self

        return None

    def find_executable_files(self, src_dir):
        # used when 'source' configuration is used, but only supports Python sources
        pass

    def has_dynamic_source_filename(self):
        # since we don't have standard .py filenames, we need the dynamic solution
        return True

    def dynamic_source_filename(self, filename, frame):
        # this method is invoked for every frame that needs to be traced
        if frame.f_code.co_name == '_found_js_cov':
            # execution has reached JsCovFind._found_js_cov, a special method used to trigger coverage of JS scripts,
            # map this trace to the specific JS
            js_fname = frame.f_locals['js_fname']
            # print('{js_cov} dynamic_source_filename: js_fname=%s' % repr(js_fname))
            return js_fname

        return None

    def line_number_range(self, frame):
        """ report which line numbers have been covered """
        if frame.f_code.co_name == '_found_js_cov':
            # js_fname = frame.f_locals['js_fname']
            # print('{js_cov} line_number_range for %s: %s, %s' % (repr(js_fname), nrs1, nrs2))
            nrs1 = frame.f_locals['range_start']
            nrs2 = frame.f_locals['range_end']
            return nrs1, nrs2
        return -1, -1

    def file_reporter(self, filename):
        """ instantiate a reporter for a specific JS file """
        # print('{js_cov} file_reporter(filename=%s)' % repr(filename))
        return JsCovFileReporter(filename)


class JsCovFileReporter(coverage.plugin.FileReporter):

    """ This class helps with the coverage report generation """

    def __init__(self, filename):
        super().__init__(filename)
        self._contents = None     # copy of the file contents, once read

    def _js_source(self):
        if self._contents is None:
            try:
                with open(self.filename, encoding="utf-8") as f:
                    self._contents = f.read()
            except (OSError, UnicodeError) as exc:
                raise NoSource("Failed to read %s: %s" % (repr(self.filename), exc))
        return self._contents

    def lines(self):
        # return the lines that can be executed
        # we use the instrumentation code to identify these line numbers
        instrument = JsCovInstrument()
        instrument.instrument(self._js_source(), 'dummy')
        return set(instrument.executable_line_nrs)


# end of file
