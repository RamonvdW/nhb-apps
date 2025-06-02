# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

class JsCovInstrument:

    """ instrument a javascript file in order to measure coverage inside the browser.

        The variable _js_cov will be populated with line numbers (of the original file) that have been reached.
    """

    # name of the global variable
    js_cov_global = 'window._js_cov'        # forced global
    js_cov_local = '_js_f'

    def __init__(self):
        self.line_nr = 0
        self.scope_stack = list()     # [c, ...] c = character that ends the scope
        self.js_cov_func = ''         # function to call to store line covered
        self.statement_line_nrs = list()
        self.executable_line_nrs = list()
        self.local_f_counter = 0

    def instrument(self, contents, app_path):
        """ Doorloop javascript en voeg extra code toe voor code coverage instrumentatie
            Verwijdert commentaarregels
        """

        if '/* js_cov: no */' in contents:
            # file is excluded from instrumentation
            return contents

        # keep the copyright header
        pos = contents.find('*/\n')
        clean = contents[:pos + 3]
        contents = contents[pos + 3:]

        self.line_nr = 1 + clean.count('\n')
        self.scope_stack = list()       # empty list = global scope
        self.statement_line_nrs = list()
        self.executable_line_nrs = list()

        self.local_f_counter += 1
        self.js_cov_func = 'js_f%s' % str(self.local_f_counter)
        const_name = 'js_c%s' % str(self.local_f_counter)

        # declare a const that holds the long filename
        clean += 'const %s = "%s";\n' % (const_name, app_path)

        clean += 'function %s(line_nr) {\n' % self.js_cov_func

        # initialize the global, if needed (on first use)
        clean += '  if (%s === undefined) { %s = {}; };\n' % (self.js_cov_global, self.js_cov_global)

        # initialize the file-specific section in the global, if needed (on first use)
        clean += '  if (%s[%s] === undefined) { %s[%s] = {}; };\n' % (self.js_cov_global, const_name,
                                                                      self.js_cov_global, const_name)

        # store the covered line
        clean += '  %s[%s][line_nr] = 1;\n' % (self.js_cov_global, const_name)

        clean += '}'

        # if it does not yet exist, create the global variable to track coverage
        # clean += 'if (typeof %s === "undefined") { var %s = {}; };\n' % (self.js_cov_global, self.js_cov_global)
        # clean += 'var %s = %s || {};\n' % (self.js_cov_global, self.js_cov_global)

        # declare a const that holds the long filename
        # clean += 'const %s = "%s";\n' % (js_cov_f_nr, app_path)

        # initialize the structure to cover the current script
        # the || {} construction avoids overwriting data
        # clean += '%s = %s || {};\n' % (self.js_cov_file, self.js_cov_file)

        while len(contents):
            # zoek strings zodat we die niet wijzigen
            pos_dq = contents.find('"')
            pos_sq = contents.find("'")

            if pos_sq >= 0 and pos_dq >= 0:
                pos_q = min(pos_sq, pos_dq)  # both not -1 --> take first, thus min
            else:
                pos_q = max(pos_sq, pos_dq)  # either one is -1 --> take max, thus the positive one

            # zoek commentaar zodat we geen quotes in commentaar pakken /* can't */
            pos_sc = contents.find('//')  # single line comment
            pos_bc = contents.find('/*')  # block comment

            if pos_sc >= 0 and pos_bc >= 0:
                pos_c = min(pos_sc, pos_bc)  # both not -1 --> take first, thus min
            else:
                pos_c = max(pos_sc, pos_bc)  # either one is -1 --> take max, thus the positive one

            if pos_c >= 0 and pos_q >= 0:
                # zowel quote and commentaar
                if pos_c < pos_q:
                    # commentaar komt eerst

                    # verwerk het stuk script voordat het commentaar begint
                    pre_comment = contents[:pos_c]
                    clean += self._instrument_part(pre_comment)
                    contents = contents[pos_c:]

                    # verwijder het commentaar
                    if pos_c == pos_sc:
                        # verwijder single-line comment
                        pos = contents.find('\n')
                        if pos > 0:
                            contents = contents[pos + 1:]
                            self.line_nr += 1
                        else:
                            contents = ''
                    else:
                        # verwijder block comment
                        pos = contents.find('*/')
                        if pos > 0:
                            comment = contents[:pos + 2]
                            self.line_nr += comment.count('\n')
                            contents = contents[pos + 2:]
                        else:
                            contents = ''

                    # opnieuw evalueren
                    continue

            if pos_q >= 0:
                pre_string = contents[:pos_q]
                clean += self._instrument_part(pre_string)

                stop_char = contents[pos_q]
                contents = contents[pos_q + 1:]  # kap pre-string en quote eraf
                pos = self._zoek_eind_quote(contents, stop_char)
                clean += stop_char  # open char
                clean_part = contents[:pos + 1]  # kopieer string inclusief stop-char
                clean += clean_part
                self.line_nr += clean_part.count('\n')
                contents = contents[pos + 1:]

            elif pos_c > 0:
                # comment, no more quotes

                # verwerk het stuk script voordat het commentaar begint
                pre_comment = contents[:pos_c]
                clean += self._instrument_part(pre_comment)
                contents = contents[pos_c:]

                # verwijder het commentaar
                if pos_c == pos_sc:
                    # verwijder single-line comment
                    pos = contents.find('\n')
                    if pos > 0:
                        contents = contents[pos + 1:]
                        self.line_nr += 1
                    else:
                        contents = ''
                else:
                    # verwijder block comment
                    pos = contents.find('*/')
                    if pos > 0:
                        comment = contents[:pos + 2]
                        self.line_nr += comment.count('\n')
                        contents = contents[pos + 2:]
                    else:
                        contents = ''

            else:
                clean += self._instrument_part(contents)
                contents = ''
        # while

        # remove empty lines
        while '\n\n' in clean:
            clean = clean.replace('\n\n', '\n')
        # while

        return clean

    def _instrument_part(self, script):
        clean = ''

        while len(script) > 0:
            pos_n = script.find('\n')
            if pos_n >= 0:
                line = script[:pos_n]
                script = script[pos_n+1:]
            else:
                line = script
                script = ''

            if line.strip() != '':
                # print('[%s] line: %s' % (self.line_nr, repr(line)))
                if self.line_nr not in self.statement_line_nrs:
                    self.statement_line_nrs.append(self.line_nr)
                    self.executable_line_nrs.append(self.line_nr)
                clean += line

                insert_here = False

                if line[-1] == ';':
                    # end of statement
                    insert_here = True

                if line[-1] == '{':
                    if 'function' in line or 'forEach' in line:
                        insert_here = True

                if insert_here:
                    # print('[%s] inserting (%s)' % (self.line_nr, repr(self.statement_line_nrs)))
                    for line_nr in self.statement_line_nrs:
                        clean += '\n%s(%s);' % (self.js_cov_func, line_nr)
                    # for
                    self.statement_line_nrs = list()

            if pos_n >= 0:
                clean += '\n'
                self.line_nr += 1
        # while

        return clean

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
