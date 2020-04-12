# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test.runner import DiscoverRunner
from unittest import TestSuite


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

    def rebuild_suite_hierarchical(self, suite):
        """ create a new test suite with the tests ordered by test_after dependencies

            a testcase is added to the new testsuite when all tests mentioned in 'test_after' have been added already.

        """
        new_suite = self.test_suite()

        tests = dict()      # [ref] = list(test, test, ..)
        after = dict()      # [ref] = test_after tuple
        for test in suite:
            if not hasattr(test, 'test_after'):
                # no test order requested
                new_suite.addTest(test)
            else:
                if type(test.test_after) != tuple:      # pragma: no cover
                    raise TypeError("Expected tuple but got test_after = %s on %s" % (type(test.test_after), repr(test)))

                ref = repr(test)[1:].split(" ")[0]      # extracts the class name

                for check in test.test_after:
                    if ref.startswith(check):           # pragma: no cover
                        raise LookupError('Circular dependency: %s.test_after depends on %s' % (ref, check))

                # store the test object
                try:
                    tests[ref].append(test)
                except KeyError:
                    tests[ref] = [test]

                # store the test dependency
                after[ref] = test.test_after
        # for

        # take over tests with no unsatisfied test dependencies
        limiter = len(after)
        while limiter > 0 and len(after) > 0:

            # print('\nlimiter=%s' % limiter)
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
