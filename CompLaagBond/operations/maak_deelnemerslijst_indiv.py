# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE, KAMP_RANK_BLANCO
from Competitie.models import Competitie
from CompKampioenschap.operations import bepaal_kamp_indiv_deelnemerslijst, zet_dirty
from CompLaagBond.models import KampBK, DeelnemerBK
from CompLaagRayon.models import DeelnemerRK


def maak_deelnemerslijst_bk_indiv(stdout, comp: Competitie):
    """ bepaal de individuele deelnemers van het BK
        per klasse zijn dit de rayonkampioenen (4x) aangevuld met de sporters met de hoogste kwalificatie scores
        iedereen die scores neergezet heeft in het RK komt in de lijst
    """

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Toegevoegd aan de BK indiv deelnemerslijst\n" % stamp_str

    if comp.is_indoor():
        aantal_pijlen = 2.0 * 30
    else:
        aantal_pijlen = 2.0 * 25

    deelkamp_bk = KampBK.objects.get(competitie=comp)

    # verwijder alle deelnemers van een voorgaande run
    DeelnemerBK.objects.filter(kamp=deelkamp_bk).delete()

    bulk = list()
    for deelnemer_rk in (DeelnemerRK
                     .objects
                     .filter(kamp__competitie=comp,
                             result_rank__lte=KAMP_RANK_BLANCO)
                     .exclude(deelname=DEELNAME_NEE)
                     .exclude(result_rank=0)
                     .select_related('kamp',
                                     'kamp__rayon',
                                     'indiv_klasse_volgende_ronde',
                                     'bij_vereniging',
                                     'sporterboog')):

        som_scores = deelnemer_rk.result_score_1 + deelnemer_rk.result_score_2
        gemiddelde = som_scores / aantal_pijlen

        if deelnemer_rk.result_score_1 > deelnemer_rk.result_score_2:
            gemiddelde_scores = "%03d%03d" % (deelnemer_rk.result_score_1, deelnemer_rk.result_score_2)
        else:
            gemiddelde_scores = "%03d%03d" % (deelnemer_rk.result_score_2, deelnemer_rk.result_score_1)

        nieuw = DeelnemerBK(
                    kamp=deelkamp_bk,
                    sporterboog=deelnemer_rk.sporterboog,
                    indiv_klasse=deelnemer_rk.indiv_klasse_volgende_ronde,
                    indiv_klasse_volgende_ronde=deelnemer_rk.indiv_klasse_volgende_ronde,
                    bij_vereniging=deelnemer_rk.bij_vereniging,
                    gemiddelde=gemiddelde,
                    gemiddelde_scores=gemiddelde_scores,
                    logboek=msg)

        if deelnemer_rk.result_rank == 1:
            nieuw.kampioen_label = 'Kampioen %s' % deelnemer_rk.kamp.rayon.naam
            nieuw.deelname = DEELNAME_JA
            nieuw.logboek += '[%s] Deelname op Ja gezet, want kampioen RK\n' % stamp_str

        bulk.append(nieuw)

        if len(bulk) >= 250:
            DeelnemerBK.objects.bulk_create(bulk)
            bulk = list()
    # for

    if len(bulk):
        DeelnemerBK.objects.bulk_create(bulk)
    del bulk

    deelkamp_bk.heeft_deelnemerslijst = True
    deelkamp_bk.save(update_fields=['heeft_deelnemerslijst'])

    # bepaal nu voor elke klasse de volgorde van de deelnemers
    # en zit iedereen boven de cut op deelname=ja

    # bepaal alle wedstrijdklassen aan de hand van de ingeschreven sporters
    for deelnemer in (DeelnemerBK
                      .objects
                      .filter(kamp=deelkamp_bk)
                      .select_related('indiv_klasse')
                      .distinct('indiv_klasse')):
        indiv_klasse = deelnemer.indiv_klasse

        stdout.write('[INFO] Bepaal deelnemers in indiv_klasse %s van %s' % (indiv_klasse, deelkamp_bk))

        bepaal_kamp_indiv_deelnemerslijst(deelkamp_bk, indiv_klasse, zet_boven_cut_op_ja=True)

        # zorg dat het google sheet bijgewerkt worden
        zet_dirty(comp.begin_jaar, int(comp.afstand),
                  rayon_nr=0, klasse_pk=indiv_klasse.pk,
                  is_bk=True, is_teams=False)
    # for

    # TODO: verstuur uitnodigingen per e-mail

    # behoud maximaal 48 sporters in elke klasse: 24 deelnemers en 24 reserves
    qset = DeelnemerBK.objects.filter(kamp=deelkamp_bk, volgorde__gt=48)
    qset.delete()


# end of file
