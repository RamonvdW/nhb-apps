# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Account.models import Account
from Competitie.models import CompetitieMatch
from CompScores.models import ExterneScoresImportLogboek
from CompScores.operations.uitslag_extern_centaur import ExterneScoresCentaur
from CompScores.operations.uitslag_extern_arrowcast import ExterneScoresArrowcast
from Vereniging.definities import TYPE_EXTERNE_SCORES_CENTAUR, TYPE_EXTERNE_SCORES_ARROWCAST
from Vereniging.models import Vereniging, ExterneScores


def comp_scores_uitslag_extern_ophalen(stdout, door_account: Account, ver: Vereniging, match: CompetitieMatch):
    ext = ExterneScores.objects.filter(is_actief=True, vereniging=ver).first()
    if not ext:
        stdout.write('[ERROR] Vereniging %s heeft geen externe scores geconfigureerd' % ver.ver_nr)
        return

    if ext.type == TYPE_EXTERNE_SCORES_CENTAUR:
        ophaler = ExterneScoresCentaur(stdout, door_account, ext, match)
    elif ext.type == TYPE_EXTERNE_SCORES_ARROWCAST:
        ophaler = ExterneScoresArrowcast(stdout, door_account, ext, match)
    else:
        stdout.write('[ERROR] ExterneScores.type %s niet geimplementeerd' % ext.type)
        return

    ophaler.ophalen()

    # regel een single-instance logboek
    import_log, _ = ExterneScoresImportLogboek.objects.get_or_create(match=match)

    if len(ophaler.errors) == 0:
        # geen fouten
        import_log.logboek = ''
    else:
        import_log.logboek = "\n".join(ophaler.errors)

    import_log.save()


# end of file
