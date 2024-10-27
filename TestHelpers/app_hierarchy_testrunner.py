# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test.runner import DiscoverRunner
from unittest import TestSuite

# totaal aantal test cases in scope van deze run
scope_count_apps = list()
scope_count_fpaths = list()
scope_count_test_cases = 0


def get_test_cases_count():
    """ Geeft terug hoeveel apps, test files en test cases in scope zijn """
    return len(scope_count_apps), len(scope_count_fpaths), scope_count_test_cases


class HierarchyRunner(DiscoverRunner):

    """ variant of the DiscoverRunner with ability to provide 'test_after' keyword in TestCase to refer to
        tests that must be run first.

        This allows a test case to indicate an hierarchical dependencies (on another functionality) built into the code.
        By running those tests first, we avoid investigating failures in underlying code.

        syntax:

            class TestMyThing(TestCase):

                test_after = ('OtherThing.test_sub',)

        Note: add a dot at the end to avoid matching 'MyApp.login' on MyApp.loginas.TestCase
    """

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        suite = super().build_suite(test_labels, extra_tests, **kwargs)
        assert isinstance(suite, TestSuite)
        return self.rebuild_suite_hierarchical(suite)

    def rebuild_suite_hierarchical(self, suite: TestSuite):
        """ create a new test suite with the tests ordered by test_after dependencies

            a testcase is added to the new testsuite when all tests mentioned in 'test_after' have been added already.

        """
        new_suite = self.test_suite()

        global scope_count_apps, scope_count_fpaths, scope_count_test_cases
        scope_count_apps = list()
        scope_count_fpaths = list()
        scope_count_test_cases = 0

        # gather all the test cases, for checking the test_after references
        known_tests = list()
        for test in suite:

            # if the suite consists of other suites, this is probably the parallel running
            if isinstance(test, TestSuite):     # pragma: no cover
                # we skip rebuilding the suite
                return suite

            test_name = test.id()           # includes the test function name

            spl = test_name.split('.')
            if len(spl) >= 4:               # pragma: no branch
                # spl parts: app, [subdirectory], file, test class, test function
                if spl[0] not in scope_count_apps:
                    scope_count_apps.append(spl[0])
                test_fpath = ".".join(spl[0:-2])
                if test_fpath not in scope_count_fpaths:
                    scope_count_fpaths.append(test_fpath)
                scope_count_test_cases += 1

            pos = test_name.rfind('.')
            test_name = test_name[:pos]     # remove the function name
            if test_name not in known_tests:
                known_tests.append(test_name)

                # also allow partial dependencies, like the complete application name
                spl = test_name.split('.')
                while len(spl) > 1:
                    spl = spl[:-1]
                    part_name = ".".join(spl)
                    if part_name not in known_tests:
                        known_tests.append(part_name)
                # while
        # for

        # print('known_tests: %s' % repr(known_tests))

        reported_warnings = list()

        tests = dict()      # [ref] = list(test, test, ..)
        after = dict()      # [ref] = test_after tuple
        for test in suite:
            if not hasattr(test, 'test_after'):
                # no test order requested
                new_suite.addTest(test)
            else:
                if type(test.test_after) is not tuple:      # pragma: no cover
                    raise TypeError("Expected tuple but got test_after = %s on %s" % (type(test.test_after),
                                                                                      repr(test)))

                ref = repr(test)[1:].split(" ")[0]      # extracts the class name

                for check in test.test_after:
                    if ref.startswith(check):           # pragma: no cover
                        raise LookupError('Circular dependency: %s.test_after depends on %s' % (ref, check))
                # for

                # store the test object
                try:
                    tests[ref].append(test)
                except KeyError:
                    tests[ref] = [test]

                # store the test dependency
                after[ref] = test.test_after

                # warn for non-existing test_after dependencies
                # in case of a partial scope run, this happens naturally, so warnings only
                for dep in test.test_after:
                    if dep[-1] == '.':      # remove terminating dot used to avoid circular dependency false positives
                        dep = dep[:-1]
                    if dep not in known_tests:      # pragma: no cover
                        warning = 'Unknown test_after dependency %s in %s' % (repr(dep), ref)
                        if warning not in reported_warnings:
                            reported_warnings.append(warning)
                            print('[WARNING] ' + warning)
                # for
        # for

        # take over tests with no unsatisfied test dependencies
        limiter = len(after)
        while limiter > 0 and len(after) > 0:

            # print('\n' + 'limiter=%s' % limiter)
            # for ref, test_after in after.items():
            #     print('%-50s %s' % (ref, test_after))

            limiter -= 1
            droprefs = list()
            remaining_tests = after.keys()
            for ref, test_after in after.items():
                awaiting_test = False
                for dep in test_after:
                    # check if this test still has to be run
                    for test in remaining_tests:
                        if test.startswith(dep):
                            awaiting_test = True
                            break
                    # for
                    if not awaiting_test:
                        break
                # for

                if not awaiting_test:
                    # these tests are ready to run
                    new_suite.addTests(tests[ref])
                    droprefs.append(ref)
            # for

            for ref in droprefs:
                del after[ref]
            # for
        # while

        if len(after) > 0:                                      # pragma: no cover
            print("Remaining test_after dependencies:")
            for ref, test_after in after.items():
                print('  %-50s %s' % (ref, test_after))
            raise LookupError("Could not resolve all test_after dependencies")

        return new_suite

# end of file
