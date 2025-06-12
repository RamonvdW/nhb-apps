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
        self.brace_level = 0
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
        self.statement_line_nrs = list()
        self.executable_line_nrs = list()
        self.brace_level = 0

        self.local_f_counter += 1
        self.js_cov_func = 'js_f%s' % str(self.local_f_counter)
        const_name = 'js_c%s' % str(self.local_f_counter)

        # declare a const that holds the long filename
        clean += 'const %s = "%s";\n' % (const_name, app_path)

        # add helper function to set coverage and handle missing variables
        if clean:
            clean += 'function %s(line_nrs) {\n' % self.js_cov_func

            # get from local storage
            clean += '  let data = localStorage.getItem("js_cov");\n'
            clean += '  let cov = {};\n'
            clean += '  if (data !== null) { cov = JSON.parse(data); }\n'

            # initialize the file-specific section, if needed (on first use)
            clean += '  if (cov[%s] === undefined) { cov[%s] = {}; }\n' % (const_name, const_name)

            # store the covered line
            clean += '  line_nrs.forEach(line_nr => { cov[%s][line_nr] = 1; });\n' % const_name

            # save to local storage
            clean += '  data = JSON.stringify(cov);\n'
            clean += '  localStorage.setItem("js_cov", data);\n'
            clean += '}\n'

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
                    clean += self._instrument_part(pre_comment, pre=clean[-50:])
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
                stop_char = contents[pos_q]
                contents = contents[pos_q + 1:]  # kap pre-string en quote eraf

                pos = self._zoek_eind_quote(contents, stop_char)
                clean_part = contents[:pos + 1]  # kopieer string inclusief stop-char

                # print('[DEBUG] clean_part = %s' % repr(clean_part))
                clean += self._instrument_part(pre_string, pre=clean[-50:])

                clean += stop_char  # open char
                clean += clean_part
                self.line_nr += clean_part.count('\n')
                contents = contents[pos + 1:]

            elif pos_c > 0:
                # comment, no more quotes

                # verwerk het stuk script voordat het commentaar begint
                pre_comment = contents[:pos_c]
                clean += self._instrument_part(pre_comment, pre=clean[-50:])
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
                clean += self._instrument_part(contents, pre=clean[-50:])
                contents = ''
        # while

        # remove empty lines
        while '\n\n' in clean:
            clean = clean.replace('\n\n', '\n')
        # while

        return clean

    def _instrument_part(self, script, pre=''):
        # script is a section of the JS code, found between comments and strings
        # possibly with newlines
        clean = ''

        # print('[DEBUG] script=%s' % repr(script))
        # if pre:
        #     print('[DEBUG] pre=%s' % repr(pre))

        use_strict_follows = pre and pre.strip()[:10] == 'use strict'

        while len(script) > 0:
            # break out a line (we want to do line coverage)
            pos_n = script.find('\n')
            if pos_n >= 0:
                line = script[:pos_n]
                script = script[pos_n+1:]
            else:
                line = script
                script = ''

            if line.strip() != '':
                line = line.rstrip()    # remove whitespace left after removing comment; keep indentation

                # pre_brace_level = self.brace_level
                self.brace_level = self.brace_level + line.count('(') + line.count('{')
                self.brace_level = self.brace_level - line.count(')') - line.count('}')
                # post_brace_level = self.brace_level
                # print('[%s][%s -> %s] line: %s' % (self.line_nr, pre_brace_level, post_brace_level, repr(line)))

                if self.brace_level > 0:        # skip closing } and });
                    if self.line_nr not in self.statement_line_nrs:
                        self.statement_line_nrs.append(self.line_nr)
                        self.executable_line_nrs.append(self.line_nr)

                insert_here = False

                if self.brace_level == 0 or "break" in line or "return" in line or "window.location.href" in line:
                    insert_here = True

                    # detect the situation where this is an inline object used as function parameter
                    # print('[%s] line=%s' % (self.line_nr, repr(line)))
                    part = pre + clean
                    part = part[-100:].strip()
                    # print('[%s] pre? part=%s' % (self.line_nr, repr(part)))
                    if part and part[-1] in ('=', ',', '[', '"', "'"):
                        insert_here = False

                if insert_here:
                    # flush before end of function
                    # print('[%s] inserting (%s)' % (self.line_nr, repr(self.statement_line_nrs)))
                    if len(self.statement_line_nrs):
                        if clean and clean[-1] != '\n':
                            clean += '\n'
                        clean += '%s(%s);\n' % (self.js_cov_func, repr(self.statement_line_nrs))
                        self.statement_line_nrs = list()

                clean += line

                insert_here = False

                if line[-1] == ';':
                    # end of statement
                    insert_here = True

                if line[-1] == '{' and not use_strict_follows:
                    # detect the situation where this is an inline object used as function parameter
                    # print('[%s] line=%s' % (self.line_nr, repr(line)))
                    part = clean[-50:-1].strip()
                    if part and (part[-1] == ')' or part[-2:] == '=>' or part[-4:] == 'else'):
                        insert_here = True
                    elif part and part[-1] in ('=', ',', '[', '"', "'"):
                        insert_here = False
                    else:
                        # if 'function' in line or 'forEach' in line or 'if ' in line or 'else' in line or 'for' in line:
                        #     print('[%s] OK part=%s' % (self.line_nr, repr(part)))
                        # else:
                        #     print('[%s] ?? part=%s' % (self.line_nr, repr(part)))
                        insert_here = True

                if insert_here:
                    # print('[%s] inserting (%s)' % (self.line_nr, repr(self.statement_line_nrs)))
                    if len(self.statement_line_nrs):
                        if clean and clean[-1] != '\n':
                            clean += '\n'
                        clean += '%s(%s);\n' % (self.js_cov_func, repr(self.statement_line_nrs))
                        self.statement_line_nrs = list()
                else:
                    # print('[%s] not inserting; line[-1] = %s' % (self.line_nr, repr(line[-1])))
                    pass

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
