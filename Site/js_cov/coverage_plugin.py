# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Site.js_cov.instrument_js import JsCovInstrument
from coverage.misc import NoSource
from collections.abc import Iterable
import coverage.plugin
import os.path
import json


class JsCoveragePluginException(Exception):
    """ Used for any errors from the plugin itself. """
    pass


class JsCoveragePlugin(coverage.plugin.CoveragePlugin,
                       coverage.plugin.FileTracer):

    def __init__(self, options):
        self.js_files = list(self._find_js_sources())
        self.js_registered = list()
        self.frame2filename = dict()
        self.js_cov_data = dict()

    @staticmethod
    def _find_js_sources():
        for dirname, _, fnames in os.walk('.'):
            # skip Site/.static/
            # skip app/static/
            if 'static/' in dirname:
                continue
            for fname in fnames:
                if fname.endswith('.js'):
                    fpath = os.path.join(dirname, fname)
                    print('{jscov} fpath=%s' % repr(fpath))
                    yield fpath
            # for
        # for

    def _load_js_cov_data(self):
        with open('/tmp/browser_js_cov.json', 'r') as f:
            data = f.read()
        self.js_cov_data = json.loads(data)

    def file_tracer(self, filename):
        if filename[-3:] == '.js':
            print('{jscov} file_tracer(filename=%s)' % repr(filename))
        # no hooking needed
        return None

    def file_reporter(self, filename):
        print('{jscov} file_reporter(filename=%s)' % repr(filename))
        return FileReporter(filename)

    # since we don't have standard .py filenames, we need the dynamic solution
    def has_dynamic_source_filename(self):
        return True

    def dynamic_source_filename(self, filename, frame):
        if len(self.js_files) > 0:
            fname = self.js_files.pop(0)
            self.js_registered.append(fname)
            print('{jscov} registering %s' % repr(fname))
            return fname

        return None

    def line_number_range(self, frame):
        print('{jscov} line_number_range(frame=%s)' % frame)
        return -1, -1
    #     assert frame.f_code.co_name in self.RENDER_METHODS
    #     if 0:
    #         dump_frame(frame, label="line_number_range")
    #
    #     render_self = frame.f_locals['self']
    #     if isinstance(render_self, (NodeList, Template)):
    #         return -1, -1
    #
    #     position = position_for_node(render_self)
    #     if position is None:
    #         return -1, -1
    #
    #     if SHOW_TRACING:
    #         print(f"{render_self!r}: {position}")
    #     s_start, s_end = position
    #     if isinstance(render_self, TextNode):
    #         first_line = render_self.s.splitlines(True)[0]
    #         if first_line.isspace():
    #             s_start += len(first_line)
    #     elif VerbatimNode and isinstance(render_self, VerbatimNode):
    #         # VerbatimNode doesn't track source the same way. s_end only points
    #         # to the end of the {% verbatim %} opening tag, not the entire
    #         # content. Adjust it to cover all of it.
    #         s_end += len(render_self.content)
    #     elif isinstance(render_self, BlockTranslateNode):
    #         # BlockTranslateNode has a list of text and variable tokens.
    #         # Get the end of the contents by looking at the last token,
    #         # and use its endpoint.
    #         last_tokens = render_self.plural or render_self.singular
    #         s_end = position_for_token(last_tokens[-1])[1]
    #
    #     filename = filename_for_frame(frame)
    #     line_map = self.get_line_map(filename)
    #     start = get_line_number(line_map, s_start)
    #     end = get_line_number(line_map, s_end-1)
    #     if start < 0 or end < 0:
    #         start, end = -1, -1
    #     if SHOW_TRACING:
    #         print("line_number_range({}) -> {}".format(
    #             filename, (start, end)
    #         ))
    #     return start, end

    # --- FileTracer helpers

    # def get_line_map(self, filename):
    #     """The line map for `filename`.
    #
    #     A line map is a list of character offsets, indicating where each line
    #     in the text begins.  For example, a line map like this::
    #
    #         [13, 19, 30]
    #
    #     means that line 2 starts at character 13, line 3 starts at 19, etc.
    #     Line 1 always starts at character 0.
    #
    #     """
    #     if filename not in self.source_map:
    #         template_source = read_template_source(filename)
    #         if 0:   # change to see the template text
    #             for i in range(0, len(template_source), 10):
    #                 print("%3d: %r" % (i, template_source[i:i+10]))
    #         self.source_map[filename] = make_line_map(template_source)
    #     return self.source_map[filename]


class FileReporter(coverage.plugin.FileReporter):

    def __init__(self, filename):
        super().__init__(filename)
        print('{jscov} FileReporter.__init__: filenames=%s' % repr(filename))

        self._contents = None     # copy of the file contents, once read

    def source(self):
        if self._contents is None:
            try:
                with open(self.filename, encoding="utf-8") as f:
                    self._contents = f.read()
            except (OSError, UnicodeError) as exc:
                raise NoSource("Failed to read %s: %s" % (repr(self.filename), exc))
        return self._contents

    def lines(self):
        instrument = JsCovInstrument()
        instrument.instrument(self.source(), 'dummy')
        return set(instrument.executable_line_nrs)

# def running_sum(seq):
#     total = 0
#     for num in seq:
#         total += num
#         yield total


# def make_line_map(text):
#     line_lengths = [len(line) for line in text.splitlines(True)]
#     line_map = list(running_sum(line_lengths))
#     return line_map


# def get_line_number(line_map, offset):
#     """Find a line number, given a line map and a character offset."""
#     for lineno, line_offset in enumerate(line_map, start=1):
#         if line_offset > offset:
#             return lineno
#     return -1


# def dump_frame(frame, label=""):
#     """Dump interesting information about this frame."""
#     locals = dict(frame.f_locals)
#     self = locals.get('self', None)
#     context = locals.get('context', None)
#     if "__builtins__" in locals:
#         del locals["__builtins__"]
#
#     if label:
#         label = " ( %s ) " % label
#     print("-- frame --%s---------------------" % label)
#     print("{}:{}:{}".format(
#         os.path.basename(frame.f_code.co_filename),
#         frame.f_lineno,
#         type(self),
#         ))
#     print(locals)
#     if self:
#         print("self:", self.__dict__)
#     if context:
#         print("context:", context.__dict__)
#     print("\\--")

# end of file
