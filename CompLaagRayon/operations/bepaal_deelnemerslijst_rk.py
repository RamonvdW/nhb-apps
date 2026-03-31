# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEELNAME_NEE, DEELNAME_ONBEKEND
from Competitie.models import Competitie, Regiocompetitie, RegiocompetitieSporterBoog
from CompKampioenschap.operations import bepaal_kamp_indiv_deelnemerslijst, zet_dirty
from CompLaagRayon.models import KampRK, DeelnemerRK, TeamRK
from Logboek.models import schrijf_in_logboek
from Taken.operations import maak_taak


def _get_regio_sporters_rayon(comp: Competitie, rayon_nr: int):
    """ geeft een lijst met deelnemers terug
        en een totaal-status van de onderliggende regiocompetities: alles afgesloten?
    """

    # sporter komen uit de 4 regio's van het rayon
    pks = list()
    for deelcomp in (Regiocompetitie
                    .objects
                    .filter(competitie=comp,
                            regio__rayon_nr=rayon_nr)):
        pks.append(deelcomp.pk)
    # for

    # TODO: sorteren en kampioenen eerst zetten kan allemaal weg, want: ...??
    deelnemers = (RegiocompetitieSporterBoog
                  .objects
                  .select_related('indiv_klasse',
                                  'bij_vereniging__regio',
                                  'sporterboog__sporter',
                                  'sporterboog__sporter__bij_vereniging',
                                  'sporterboog__sporter__bij_vereniging__regio__rayon')
                  .filter(regiocompetitie__in=pks,
                          aantal_scores__gte=comp.aantal_scores_voor_rk_deelname,
                          indiv_klasse__is_ook_voor_rk_bk=True)  # skip aspiranten
                  .order_by('indiv_klasse__volgorde',  # groepeer per klasse
                            '-gemiddelde'))  # aflopend gemiddelde

    # markeer de regiokampioenen
    klasse = -1
    regio_score = dict()   # [regio] = score  --> bijhouden welke kampioenen we al gemarkeerd hebben, meerdere #1 mogelijk
    kampioenen = list()
    deelnemers = list(deelnemers)
    nr = 0
    insert_at = 0
    rank = 0
    while nr < len(deelnemers):
        deelnemer = deelnemers[nr]

        if klasse != deelnemer.indiv_klasse.volgorde:
            klasse = deelnemer.indiv_klasse.volgorde
            if len(kampioenen):
                kampioenen.sort()       # TODO: sortering niet gelijk aan sortering net buiten while lus
                for tup in kampioenen:
                    kampioen = tup[-1]
                    deelnemers.insert(insert_at, kampioen)
                    insert_at += 1
                    nr += 1
                # for
            kampioenen = list()
            regio_score = dict()
            insert_at = nr
            rank = 0

        # fake een paar velden uit KampioenschapSporterBoog
        rank += 1
        deelnemer.volgorde = rank
        deelnemer.deelname = DEELNAME_ONBEKEND

        scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                  deelnemer.score5, deelnemer.score6, deelnemer.score7]
        scores.sort(reverse=True)  # beste score eerst
        deelnemer.regio_scores = "%03d%03d%03d%03d%03d%03d%03d" % tuple(scores)

        regio_nr = deelnemer.bij_vereniging.regio.regio_nr
        prev_score = regio_score.get(regio_nr, None)
        if not prev_score or deelnemer.totaal == prev_score:
            regio_score[regio_nr] = deelnemer.totaal
            deelnemer.kampioen_label = "Kampioen regio %s" % regio_nr
            tup = (regio_nr, deelnemer.pk, deelnemer)
            kampioenen.append(tup)
            deelnemers.pop(nr)
        else:
            # alle sporters overnemen als potentiële reserve-sporter
            deelnemer.kampioen_label = ""
            nr += 1
    # while

    if len(kampioenen):
        kampioenen.sort(reverse=True)  # hoogste regionummer bovenaan
        for tup in kampioenen:
            kampioen = tup[-1]
            deelnemers.insert(insert_at, kampioen)
            insert_at += 1
        # for

    return deelnemers


def bepaal_deelnemers_rk_indiv(stdout, comp: Competitie):
    """ maak de individuele deelnemers voor de RKs aan de hand van de regiocompetitie resultaten
        ook wordt hier de vereniging van de sporter bevroren.

        voor elke klasse wordt de dirty vlag gezet.
        er wordt geen mutatie gemaakt voor de update van dirty formulieren.
    """

    # verwijder alle eerder gekoppelde team leden
    for team in TeamRK.objects.filter(kamp__competitie=comp):
        team.gekoppelde_leden.clear()
    # for
    DeelnemerRK.objects.filter(kamp__competitie=comp).all().delete()

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
    msg = "[%s] Toegevoegd aan de RK indiv deelnemerslijst\n" % stamp_str

    # sporters moeten in het rayon van hun huidige vereniging geplaatst worden
    rayon_nr2deelkamp = dict()
    for kamp_rk in (KampRK
                        .objects
                        .select_related('rayon')
                        .filter(competitie=comp)):
        rayon_nr2deelkamp[kamp_rk.rayon.rayon_nr] = kamp_rk
    # for

    for kamp_rk in (KampRK
                        .objects
                        .select_related('rayon')
                        .filter(competitie=comp)):

        deelnemers = _get_regio_sporters_rayon(comp, kamp_rk.rayon.rayon_nr)

        # schrijf all deze sporters in voor het RK
        # kampioenen als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
        bulk_lijst = list()
        for deelnemer in deelnemers:

            # sporter moet nu lid zijn bij een vereniging
            ver = deelnemer.sporterboog.sporter.bij_vereniging
            if ver:
                # schrijf de sporter in het juiste rayon in
                kamp_rk = rayon_nr2deelkamp[ver.regio.rayon_nr]

                kampioen = DeelnemerRK(
                                kamp=kamp_rk,
                                sporterboog=deelnemer.sporterboog,
                                indiv_klasse=deelnemer.indiv_klasse,
                                indiv_klasse_volgende_ronde=deelnemer.indiv_klasse,
                                bij_vereniging=ver,  # bevries vereniging
                                kampioen_label=deelnemer.kampioen_label,
                                gemiddelde=deelnemer.gemiddelde,
                                gemiddelde_scores=deelnemer.regio_scores,
                                logboek=msg)

                if not deelnemer.inschrijf_voorkeur_rk_bk:
                    # bij inschrijven al afgemeld voor RK/BK
                    kampioen.deelname = DEELNAME_NEE
                    kampioen.logboek += '[%s] Deelname op Nee gezet want geen voorkeur RK/BK\n' % stamp_str

                bulk_lijst.append(kampioen)
                if len(bulk_lijst) > 150:  # pragma: no cover
                    DeelnemerRK.objects.bulk_create(bulk_lijst)
                    bulk_lijst = list()
            else:
                stdout.write('[WARNING] Sporter %s is geen RK deelnemer want heeft geen vereniging' %
                             deelnemer.sporterboog)
        # for

        if len(bulk_lijst) > 0:
            DeelnemerRK.objects.bulk_create(bulk_lijst)
        del bulk_lijst
    # for

    for kamp_rk in (KampRK
                    .objects
                    .select_related('rayon')
                    .filter(competitie=comp)
                    .order_by('rayon__rayon_nr')):

        # bepaal de deelnemerslijst voor elke klasse
        for deelnemer in (DeelnemerRK
                          .objects
                          .filter(kamp=kamp_rk)
                          .select_related('indiv_klasse')
                          .distinct('indiv_klasse')):

            stdout.write('[INFO] Bepaal deelnemers in indiv_klasse %s van %s' % (deelnemer.indiv_klasse,
                                                                                 kamp_rk))

            bepaal_kamp_indiv_deelnemerslijst(kamp_rk, deelnemer.indiv_klasse, zet_boven_cut_op_ja=False)

            # zorg dat het google sheet bijgewerkt worden
            zet_dirty(comp.begin_jaar, int(comp.afstand),
                      kamp_rk.rayon.rayon_nr,
                      deelnemer.indiv_klasse.pk,
                      is_bk=False, is_teams=False)
        # for

        kamp_rk.heeft_deelnemerslijst = True
        kamp_rk.save(update_fields=['heeft_deelnemerslijst'])

        # stuur de RKO een taak ('ter info')
        functie_rko = kamp_rk.functie
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now
        taak_onderwerp = "Deelnemerslijsten RK zijn vastgesteld"
        taak_tekst = "Ter info: De deelnemerslijsten voor jouw Rayonkampioenschappen zijn vastgesteld door de BKO"
        taak_log = "[%s] Taak aangemaakt" % stamp_str

        # maak een taak aan voor deze BKO
        maak_taak(toegekend_aan_functie=functie_rko,
                  deadline=taak_deadline,
                  aangemaakt_door=None,  # systeem
                  onderwerp=taak_onderwerp,
                  beschrijving=taak_tekst,
                  log=taak_log)

        # schrijf in het logboek
        msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(kamp_rk.rayon)
        msg += '\nDe %s is geïnformeerd via een taak' % functie_rko
        schrijf_in_logboek(None, "Competitie", msg)
    # for


# end of file
