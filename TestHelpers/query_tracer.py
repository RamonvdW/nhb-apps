# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

import traceback
import time

"""

Usage:

    @contextmanager
    def some_fund(self, modify_acceptable=False):
        tracer = MyQueryTracer(modify_acceptable)
        try:
            with connection.execute_wrapper(tracer):
                yield
        finally:
            # analyze results
            duration = get_elapsed_seconds()
            count = len(tracer.trace)
            ...

"""

# debug optie: toon waar in de code de queries vandaan komen
REPORT_QUERY_ORIGINS = False


class MyQueryTracer(object):
    def __init__(self, modify_acceptable=False):
        self.trace = list()             # [dict, dict, ..] Keys: sql, now, duration_us, stack
        self.started_at_ns = time.monotonic_ns()
        self.total_duration_us = 0
        self.stack_counts = dict()      # [stack] = count       requires REPORT_QUERY_ORIGINS = True
        self.modify_acceptable = modify_acceptable
        self.found_modify = False       # meer dan SELECT gevonden
        self.found_code = ""            # view function filename, line, name
        self.found_500 = False

    def __call__(self, execute, sql, params, many, context):
        call = {'sql': sql}
        # print('sql:', sql)            # query with some %s in it
        # print('params:', params)      # params for the %s ?
        # print('many:', many)          # true/false

        time_start = time.monotonic_ns()
        call['now'] = time_start

        execute(sql, params, many, context)

        time_end = time.monotonic_ns()
        time_delta_ns = time_end - time_start
        duration_us = int(time_delta_ns / 1000)
        call['duration_us'] = duration_us
        self.total_duration_us += duration_us

        call['stack'] = stack = list()
        for fname, line_nr, base, code in traceback.extract_stack():
            # print(base, fname, line_nr, code)
            if (base != '__call__'
                    and not fname.startswith('/usr/lib')
                    and '<frozen' not in fname
                    and '/site-packages/' not in fname
                    and 'manage.py' not in fname):
                stack.append((fname, line_nr, base))

                if base == 'site_handler500_internal_server_error':
                    self.found_500 = True
                    break   # from the for

                # houd bij vanuit welke view functie
                if '/view' in fname and self.found_code == '':
                    if 'post' in base or 'get' in base or 'test_func' in base:
                        if 'SELECT ' not in sql and 'SAVEPOINT ' not in sql:
                            self.found_code = "%s in %s:%s" % (base, fname, line_nr)
                            # print(sql[:40], self.found_code)
            elif base == 'render' and 'template/response.py' in fname:
                stack.append((fname, line_nr, base))

            # print(fname, line_nr, base)
            if base == 'post':                  # naam van functie is 'post'
                self.modify_acceptable = True
            elif base == 'call_command':        # standaard Django functie om management command uit te voeren
                self.modify_acceptable = True
        # for
        # print('call stack:\n  ', "\n  ".join([str(tup) for tup in stack]))

        if REPORT_QUERY_ORIGINS:                        # pragma: no cover
            msg = ''
            for fname, line_nr, base in stack:
                msg += '\n         %s:%s %s' % (fname[-35:], line_nr, base)
            try:
                self.stack_counts[msg] += 1
            except KeyError:
                self.stack_counts[msg] = 1

        if not sql.startswith('SELECT '):
            ignore = False

            # ignore SAVEPOINT and RELEASE SAVEPOINT
            if "SAVEPOINT " in sql:
                ignore = True

            # ignore UPDATE "django_session"
            if "django_session" in sql:
                ignore = True

            if not ignore:
                self.found_modify = True

        self.trace.append(call)

    @staticmethod
    def _find_statement(query, start):          # pragma: no cover
        best = -1
        word_len = 0
        for word in (  # 'SELECT', 'DELETE FROM', 'INSERT INTO',
                     ' WHERE ', ' LEFT OUTER JOIN ', ' INNER JOIN ', ' LEFT JOIN ', ' JOIN ',
                     ' ORDER BY ', ' GROUP BY ', ' ON ', ' FROM ', ' VALUES '):
            pos = query.find(word, start)
            if pos >= 0 and (best == -1 or pos < best):
                best = pos
                word_len = len(word)
        # for
        return best, word_len

    def _reformat_sql(self, prefix, query):     # pragma: no cover
        start = 0
        pos, word_len = self._find_statement(query, start)
        prefix = prefix[:-1]        # because pos starts with a space
        while pos >= 0:
            query = query[:pos] + prefix + query[pos:]
            start = pos + word_len + len(prefix)
            pos, word_len = self._find_statement(query, start)
        # while
        return query

    def __str__(self):                          # pragma: no cover
        """ wordt gebruikt als er te veel queries zijn """
        queries = 'Captured queries:'
        prefix = '\n       '
        limit = 200  # begrens aantal queries dat we printen
        for i, call in enumerate(self.trace, start=1):
            if i > 1:
                queries += '\n'
            queries += prefix + str(call['now'])
            queries += '\n [%d]  ' % i
            queries += self._reformat_sql(prefix, call['sql'])
            queries += prefix + '%s µs' % call['duration_us']
            queries += '\n'
            for fname, line_nr, base in call['stack']:
                queries += prefix + '%s:%s   %s' % (fname, line_nr, base)
            # for
            limit -= 1
            if limit <= 0:
                break
        # for
        return queries

    def report(self):
        report = []
        if REPORT_QUERY_ORIGINS:                        # pragma: no cover
            # sorteer op aantal aanroepen
            counts = list()
            for msg, count in self.stack_counts.items():
                tup = (count, msg)
                counts.append(tup)
            # for
            counts.sort(reverse=True)       # hoogste eerst
            first = True
            for count, msg in counts:
                if count > 1:
                    if first:
                        first = False
                        report.append('-----')
                    report.append('%5s %s' % (count, msg[7:]))
            # for
        return "\n".join(report)

    def get_elapsed_seconds(self):
        duration_ns = time.monotonic_ns() - self.started_at_ns
        duration_sec = duration_ns / 1000000000
        # print("duration_ns=%s --> duration_sec=%s" % (duration_ns, duration_sec))
        return duration_sec

# end of file
