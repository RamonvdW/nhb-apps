# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.core import management
from django.test import TestCase, override_settings
from Site.core.main_exceptions import SpecificExitCode
import io


class MyMgmtCommandHelper(TestCase):

    """ Helpers om de response pagina's te controleren op status en inhoud

        mixin class voor django.test.TestCase
    """

    def run_management_command(self, *args, report_exit_code=True):
        """ Helper om code duplicate te verminderen en bij een SystemExit toch de traceback (in stderr) te tonen """
        f1 = io.StringIO()
        f2 = io.StringIO()
        try:
            management.call_command(*args, stderr=f1, stdout=f2)
        except (SystemExit, SpecificExitCode, Exception) as exc:
            if report_exit_code:                # pragma: no cover
                msg = '\n'
                msg += '{run_management_command} caught %s\n' % repr(exc)
                msg += 'commando: %s\n' % repr(args)
                msg += 'stderr:\n'
                msg += f1.getvalue()
                msg = msg.replace('\n', '\n  ')
                raise self.failureException(msg) from exc
            else:
                f1.write('[TEST] Management command raised %s\n' % repr(exc))
        return f1, f2

    def verwerk_competitie_mutaties(self, show_warnings=True, show_all=False):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()
        management.call_command('competitie_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        err_msg = f1.getvalue()
        if '[ERROR]' in err_msg or 'Traceback:' in err_msg:  # pragma: no cover
            self.fail(msg='Onverwachte fout van competitie_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

        return f1, f2

    def verwerk_bestel_mutaties(self, kosten_pakket=6.75, kosten_brief=4.04,
                                show_warnings=True, show_all=False, fail_on_error=True):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()

        with override_settings(WEBWINKEL_PAKKET_GROOT_VERZENDKOSTEN_EURO=kosten_pakket,
                               WEBWINKEL_BRIEF_VERZENDKOSTEN_EURO=kosten_brief):
            management.call_command('bestel_mutaties', '1', '--quick', stderr=f1, stdout=f2)

        if fail_on_error:
            err_msg = f1.getvalue()
            if '[ERROR]' in err_msg or 'Traceback:' in err_msg:                 # pragma: no cover
                self.fail(msg='Onverwachte fout van bestel_mutaties:\n' + err_msg)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        elif show_warnings:                                                     # pragma: no branch
            lines = f1.getvalue() + '\n' + f2.getvalue()
            for line in lines.split('\n'):
                if line.startswith('[WARNING] '):                               # pragma: no cover
                    print(line)
            # for

        return f1, f2

    @staticmethod
    def verwerk_betaal_mutaties(seconden=1, show_all=False):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()

        management.call_command('betaal_mutaties', str(0 + seconden), '--quick', stderr=f1, stdout=f2)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        return f1, f2

    @staticmethod
    def verwerk_scheids_mutaties(seconden=1, show_all=False):
        # vraag de achtergrondtaak om de mutaties te verwerken
        f1 = io.StringIO()
        f2 = io.StringIO()

        management.call_command('scheids_mutaties', str(0 + seconden), '--quick', stderr=f1, stdout=f2)

        if show_all:                                                            # pragma: no cover
            print(f1.getvalue())
            print(f2.getvalue())

        return f1, f2

# end of file
