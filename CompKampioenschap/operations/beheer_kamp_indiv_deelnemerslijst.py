# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from django.db.models import F, ObjectDoesNotExist
from Competitie.definities import DEELNAME_JA, DEELNAME_NEE
from Competitie.models import CompetitieIndivKlasse
from CompLaagBond.models import KampBK, DeelnemerBK, CutBK
from CompLaagRayon.models import KampRK, DeelnemerRK, CutRK

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField


def _get_limiet_indiv(deelkamp: KampRK | KampBK,
                      indiv_klasse: CompetitieIndivKlasse):
    # haal de limiet uit de database, indien aanwezig
    if isinstance(deelkamp, KampRK):
        cut = CutRK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse).first()
    else:
        cut = CutBK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse).first()

    limiet = cut.limiet if cut else 24  # fallback = 24
    return limiet


def bepaal_kamp_indiv_deelnemerslijst(deelkamp: KampRK | KampBK,
                                      indiv_klasse: CompetitieIndivKlasse,
                                      zet_boven_cut_op_ja: bool = False):
    # Bepaal de top-X deelnemers voor een klasse van een kampioenschap
    # De kampioenen aangevuld met de sporters met hoogste gemiddelde
    # gesorteerde op gemiddelde

    limiet = _get_limiet_indiv(deelkamp, indiv_klasse)

    if isinstance(deelkamp, KampRK):
        qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp)
    else:
        qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp)

    # kampioenen hebben deelnamegarantie
    kampioenen = (qset_deelnemers
                  .exclude(kampioen_label='')
                  .filter(indiv_klasse=indiv_klasse))

    lijst = list()
    aantal = 0
    for obj in kampioenen:
        if obj.deelname != DEELNAME_NEE:
            aantal += 1
        tup = (obj.gemiddelde, len(lijst), obj)
        lijst.append(tup)
    # for

    # aanvullen met sporters tot aan de cut
    objs = (qset_deelnemers
            .filter(indiv_klasse=indiv_klasse,
                    kampioen_label='')  # kampioenen hebben we al gedaan
            .order_by('-gemiddelde',  # hoogste boven
                      '-gemiddelde_scores'))  # hoogste boven (gelijk gemiddelde)

    for obj in objs:
        tup = (obj.gemiddelde, len(lijst), obj)
        lijst.append(tup)
        if obj.deelname != DEELNAME_NEE:
            aantal += 1
            if aantal >= limiet:
                break  # uit de for
    # for

    # sorteer op gemiddelde en daarna op de positie in de lijst (want sorteren op obj gaat niet)
    lijst.sort(reverse=True)

    # volgorde uitdelen voor deze kandidaat-deelnemers
    pks = list()
    volgorde = 0
    rank = 0
    for _, _, obj in lijst:
        volgorde += 1
        obj.volgorde = volgorde

        if obj.deelname == DEELNAME_NEE:
            obj.rank = 0
        else:
            rank += 1
            obj.rank = rank
            if zet_boven_cut_op_ja:
                obj.deelname = DEELNAME_JA

        obj.save(update_fields=['rank', 'volgorde', 'deelname'])
        pks.append(obj.pk)
    # for

    # geef nu alle andere sporters (onder de cut) een nieuw volgnummer
    # dit voorkomt dubbele volgnummers als de cut omlaag gezet is
    for obj in objs:
        if obj.pk not in pks:
            volgorde += 1
            obj.volgorde = volgorde

            if obj.deelname == DEELNAME_NEE:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save(update_fields=['rank', 'volgorde'])
    # for


def _update_rank_nummers(deelkamp: KampRK | KampBK,
                         klasse : CompetitieIndivKlasse):

    if isinstance(deelkamp, KampRK):
        qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp)
    else:
        qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp)

    rank = 0
    for obj in (qset_deelnemers
                .filter(indiv_klasse=klasse)
                .order_by('volgorde')):

        old_rank = obj.rank

        if obj.deelname == DEELNAME_NEE:
            obj.rank = 0
        else:
            rank += 1
            obj.rank = rank

        if obj.rank != old_rank:
            obj.save(update_fields=['rank'])
    # for

def kamp_deelnemer_afmelden(stdout, door: str, deelnemer: DeelnemerRK | DeelnemerBK):
    # de deelnemer is al afgemeld en behoudt zijn 'volgorde' zodat de RKO/BKO
    # 'm in grijs kan zien in de tabel

    # bij een mutatie "boven de cut" wordt de 1e reserve tot deelnemer gepromoveerd.
    # hiervoor wordt zijn 'volgorde' aangepast en schuift iedereen met een lager gemiddelde een plekje omlaag

    # daarna wordt de 'rank' aan voor alle sporters in deze klasse opnieuw vastgesteld

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    msg = '[%s] Mutatie door %s\n' % (stamp_str, door)
    deelnemer.logboek += msg

    msg = '[%s] Deelname op Nee gezet\n' % stamp_str
    deelnemer.deelname = DEELNAME_NEE
    deelnemer.logboek += msg
    deelnemer.save(update_fields=['deelname', 'logboek'])
    stdout.write('[INFO] Afmelding voor (rank=%s, volgorde=%s): %s' % (deelnemer.rank, deelnemer.volgorde,
                                                                       deelnemer.sporterboog))

    deelkamp = deelnemer.kamp
    if isinstance(deelkamp, KampRK):
        qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelnemer.kamp)
    else:
        qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelnemer.kamp)

    indiv_klasse = deelnemer.indiv_klasse

    limiet = _get_limiet_indiv(deelnemer.kamp, indiv_klasse)

    # haal de 1e reserve op
    try:
        reserve = (qset_deelnemers
                   .get(indiv_klasse=indiv_klasse,
                        rank=limiet+1))                 # TODO: dit faalde een keer met 2 resultaten!
    except ObjectDoesNotExist:
        # zoveel sporters zijn er niet (meer)
        pass
    else:
        if reserve.volgorde > deelnemer.volgorde:
            # de afgemelde deelnemer zat binnen de cut
            # maar de 1e reserve nu deelnemer

            stdout.write('[INFO] Reserve (rank=%s, volgorde=%s) wordt deelnemer: %s' % (
                                reserve.rank, reserve.volgorde, reserve.sporterboog))

            # het kan zijn dat de 1e reserve een flinke sprong gaat maken in de lijst
            # het kan zijn dat de 1e reserve op zijn plekje blijft staan

            # bepaal het nieuwe plekje op de deelnemers-lijst
            # rank = 1..limiet-1
            slechter = (qset_deelnemers
                        .filter(indiv_klasse=indiv_klasse,
                                gemiddelde__lt=reserve.gemiddelde,
                                rank__lte=limiet,
                                volgorde__lt=reserve.volgorde)
                        .order_by('volgorde'))      # 10, 11, 12, etc.

            if len(slechter) > 0:

                # zet het nieuwe plekje
                reserve.volgorde = slechter[0].volgorde
                reserve.logboek += '[%s] Reserve wordt deelnemer\n' % stamp_str
                reserve.save(update_fields=['volgorde', 'logboek'])

                stdout.write('[INFO] Reserve krijgt nieuwe volgorde=%s' % reserve.volgorde)

                stdout.write('[INFO] %s deelnemers krijgen volgorde+1' % len(slechter))

                # schuif de andere sporters omlaag
                slechter.update(volgorde=F('volgorde') + 1)

            # else: geen sporters om op te schuiven

    _update_rank_nummers(deelkamp, indiv_klasse)


def kamp_deelnemer_opnieuw_aanmelden(stdout, deelnemer: DeelnemerRK | DeelnemerBK):
    # meld de deelnemer opnieuw aan door hem bij de reserves te zetten

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    # sporter wordt van zijn oude 'volgorde' weggehaald
    # iedereen schuift een plekje op
    # daarna wordt de sporter op de juiste plaats ingevoegd
    # en iedereen met een lager gemiddelde schuift weer een plekje op

    if isinstance(deelnemer, DeelnemerRK):
        deelnemer_qset = DeelnemerRK.objects.filter(kamp=deelnemer.kamp)
    else:
        deelnemer_qset = DeelnemerBK.objects.filter(kamp=deelnemer.kamp)

    indiv_klasse = deelnemer.indiv_klasse
    oude_volgorde = deelnemer.volgorde

    stdout.write('[INFO] Opnieuw aanmelden vanuit oude volgorde=%s: %s' % (oude_volgorde,
                                                                           deelnemer.sporterboog))

    # verwijder de deelnemer uit de lijst op zijn oude plekje
    # en schuif de rest omhoog
    deelnemer.volgorde = VOLGORDE_PARKEER
    deelnemer.save(update_fields=['volgorde'])

    qset = (deelnemer_qset
            .filter(indiv_klasse=indiv_klasse,
                    volgorde__gt=oude_volgorde,
                    volgorde__lt=VOLGORDE_PARKEER))
    qset.update(volgorde=F('volgorde') - 1)

    limiet = _get_limiet_indiv(deelnemer.kamp, indiv_klasse)

    # als er minder dan limiet deelnemers zijn, dan invoegen op gemiddelde
    # als er een reserve lijst is, dan invoegen in de reserve-lijst op gemiddelde
    # altijd invoegen NA sporters met gelijkwaarde gemiddelde

    deelnemers_count = (deelnemer_qset
                        .exclude(deelname=DEELNAME_NEE)
                        .filter(indiv_klasse=indiv_klasse,
                                rank__lte=limiet,
                                volgorde__lt=VOLGORDE_PARKEER).count())

    if deelnemers_count >= limiet:
        # er zijn genoeg sporters, dus deze her-aanmelding moet op de reserve-lijst
        stdout.write('[INFO] Naar de reserve-lijst')
        deelnemer.logboek += '[%s] Naar de reserve-lijst\n' % stamp_str

        # zoek een plekje in de reserve-lijst
        objs = (deelnemer_qset
                .filter(indiv_klasse=indiv_klasse,
                        rank__gt=limiet,
                        gemiddelde__gte=deelnemer.gemiddelde)
                .order_by('gemiddelde',
                          'gemiddelde_scores'))

        if len(objs):
            # invoegen na de reserve-sporter met gelijk of hoger gemiddelde
            stdout.write('[INFO] Gemiddelde=%s, limiet=%s; 1e reserve heeft rank=%s, volgorde=%s' % (
                             deelnemer.gemiddelde, limiet, objs[0].rank, objs[0].volgorde))
            nieuwe_rank = objs[0].rank + 1
        else:
            # er zijn geen reserve-sporters met gelijk of hoger gemiddelde
            # dus deze sporter mag boven aan de reserve-lijst
            stdout.write('[INFO] Maak 1e reserve')
            nieuwe_rank = limiet + 1

        # maak een plekje in de lijst door andere sporters op te schuiven
        objs = (deelnemer_qset
                .filter(indiv_klasse=indiv_klasse,
                        rank__gte=nieuwe_rank))

        if len(objs) > 0:
            obj = objs.order_by('volgorde')[0]
            nieuwe_volgorde = obj.volgorde
        else:
            # niemand om op te schuiven - zet aan het einde
            nieuwe_volgorde = (deelnemer_qset
                               .exclude(volgorde=VOLGORDE_PARKEER)
                               .filter(indiv_klasse=indiv_klasse)
                               .count()) + 1
    else:
        stdout.write('[INFO] Naar deelnemers-lijst')
        deelnemer.logboek += '[%s] Direct naar de deelnemerslijst\n' % stamp_str

        # er is geen reserve-lijst in deze klasse
        # de sporter gaat dus meteen de deelnemers lijst in
        objs = (deelnemer_qset
                .filter(indiv_klasse=indiv_klasse,
                        gemiddelde__gte=deelnemer.gemiddelde,
                        volgorde__lt=VOLGORDE_PARKEER)
                .order_by('gemiddelde',
                          'gemiddelde_scores'))

        if len(objs) > 0:
            # voeg de sporter in na de laatste deelnemer
            nieuwe_volgorde = objs[0].volgorde + 1
        else:
            # geen betere sporter gevonden
            # zet deze deelnemer boven aan de lijst
            nieuwe_volgorde = 1

    stdout.write('[INFO] Nieuwe volgorde=%s' % nieuwe_volgorde)

    objs = (deelnemer_qset
            .filter(indiv_klasse=indiv_klasse,
                    volgorde__gte=nieuwe_volgorde))
    objs.update(volgorde=F('volgorde') + 1)

    deelnemer.volgorde = nieuwe_volgorde
    deelnemer.deelname = DEELNAME_JA
    deelnemer.logboek += '[%s] Deelname op Ja gezet\n' % stamp_str
    deelnemer.save(update_fields=['volgorde', 'deelname', 'logboek'])

    # deel de rank nummers opnieuw uit
    _update_rank_nummers(deelnemer.kamp, indiv_klasse)


def _indiv_verhoog_cut(deelkamp: KampRK | KampBK,
                       klasse: CompetitieIndivKlasse,
                       cut_nieuw: int):
    # de deelnemerslijst opnieuw sorteren op gemiddelde
    # dit is nodig omdat kampioenen naar boven geplaatst kunnen zijn bij het verlagen van de cut
    # nu plaatsen we ze weer terug op hun originele plek

    if isinstance(deelkamp, KampRK):
        qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp, indiv_klasse=klasse)
    else:
        qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp, indiv_klasse=klasse)

    lijst = list()
    for obj in (qset_deelnemers
                .filter(rank__lte=cut_nieuw)):
        tup = (obj.gemiddelde, len(lijst), obj)
        lijst.append(tup)
    # for

    # sorteer de deelnemers op gemiddelde (hoogste eerst)
    # bij gelijk gemiddelde: sorteer daarna op het volgnummer (hoogste eerst) in de lijst
    #                        want sorteren op obj gaat niet
    lijst.sort(reverse=True)

    # volgorde uitdelen voor deze kandidaat-deelnemers
    volgorde = 0
    rank = 0
    for _, _, obj in lijst:
        volgorde += 1
        obj.volgorde = volgorde

        if obj.deelname == DEELNAME_NEE:
            obj.rank = 0
        else:
            rank += 1
            obj.rank = rank
        obj.save(update_fields=['rank', 'volgorde'])
    # for


def _indiv_verlaag_cut(deelkamp: KampRK | KampBK,
                       indiv_klasse: CompetitieIndivKlasse,
                       cut_oud: int, cut_nieuw: int):
    # zoek de kampioenen die al deel mochten nemen (dus niet op reserve lijst)

    if isinstance(deelkamp, KampRK):
        qset_deelnemers = DeelnemerRK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse)
    else:
        qset_deelnemers = DeelnemerBK.objects.filter(kamp=deelkamp, indiv_klasse=indiv_klasse)

    kampioenen = (qset_deelnemers
                  .exclude(kampioen_label='')
                  .filter(rank__lte=cut_oud))  # begrens tot deelnemerslijst

    aantal = 0  # telt het aantal deelnemers
    lijst = list()
    lijst_pks = list()
    for obj in kampioenen:
        tup = (obj.gemiddelde, len(lijst), obj)
        lijst.append(tup)
        lijst_pks.append(obj.pk)
        if obj.deelname != DEELNAME_NEE:
            aantal += 1
    # for

    # aanvullen met sporters tot aan de cut
    if isinstance(deelkamp, KampRK):
        objs = (qset_deelnemers
                .filter(kampioen_label='',          # kampioenen hebben we al gedaan
                        rank__lte=cut_oud)
                .order_by('-gemiddelde',            # hoogste boven
                          '-gemiddelde_scores'))    # hoogste boven (bij gelijk gemiddelde)
    else:
        objs = (qset_deelnemers
                .filter(kampioen_label='',          # kampioenen hebben we al gedaan
                        rank__lte=cut_oud)
                .order_by('-gemiddelde'))           # hoogste boven

    for obj in objs:
        if obj.pk not in lijst_pks and aantal < cut_nieuw:
            # voeg deze niet-kampioen toe aan de deelnemers lijst
            tup = (obj.gemiddelde, len(lijst), obj)
            lijst.append(tup)
            lijst_pks.append(obj.pk)
            if obj.deelname != DEELNAME_NEE:
                aantal += 1
    # for

    # sorteer de deelnemers op gemiddelde (hoogste eerst)
    # bij gelijk gemiddelde: sorteer daarna op het volgnummer (hoogste eerst) in de lijst
    #                        want sorteren op obj gaat niet
    lijst.sort(reverse=True)

    # volgorde uitdelen voor deze kandidaat-deelnemers
    volgorde = 0
    rank = 0
    for _, _, obj in lijst:
        volgorde += 1
        obj.volgorde = volgorde

        if obj.deelname == DEELNAME_NEE:
            obj.rank = 0
        else:
            rank += 1
            obj.rank = rank
        obj.save(update_fields=['rank', 'volgorde'])
    # for

    # geef nu alle andere sporters (tot de oude cut) opnieuw een volgnummer
    # dit is nodig omdat de kampioenen er tussenuit gehaald (kunnen) zijn
    # en we willen geen dubbele volgnummers
    for obj in objs:
        if obj.pk not in lijst_pks:
            volgorde += 1
            obj.volgorde = volgorde

            if obj.deelname == DEELNAME_NEE:
                obj.rank = 0
            else:
                rank += 1
                obj.rank = rank
            obj.save(update_fields=['rank', 'volgorde'])
    # for


# end of file
