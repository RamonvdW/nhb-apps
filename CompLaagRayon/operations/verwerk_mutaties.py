# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.utils import timezone
from Competitie.definities import DEEL_RK, DEELNAME_NEE, DEELNAME_ONBEKEND
from Competitie.models import (Competitie,
                               Regiocompetitie, RegiocompetitieSporterBoog,
                               Kampioenschap, KampioenschapSporterBoog, KampioenschapTeam)
from CompKamp.operations.verwerk_mutaties import VerwerkCompKampMutaties
from Logboek.models import schrijf_in_logboek
from Taken.operations import maak_taak


class VerwerkCompLaagRayonMutaties:

    """
        Afhandeling van de mutatie verzoeken voor de CompLaagRegio applicatie.
        Wordt aangeroepen door de competitie_mutaties achtergrondtaak, welke gelijktijdigheid voorkomt.
    """

    def __init__(self, stdout, logger):
        self.stdout = stdout
        self.my_logger = logger

        self.kamp_mutaties = VerwerkCompKampMutaties(stdout, logger)

    @staticmethod
    def _get_regio_sporters_rayon(competitie, rayon_nr):
        """ geeft een lijst met deelnemers terug
            en een totaal-status van de onderliggende regiocompetities: alles afgesloten?
        """

        # sporter komen uit de 4 regio's van het rayon
        pks = list()
        for deelcomp in (Regiocompetitie
                         .objects
                         .filter(competitie=competitie,
                                 regio__rayon_nr=rayon_nr)):
            pks.append(deelcomp.pk)
        # for

        # TODO: sorteren en kampioenen eerst zetten kan allemaal weg
        deelnemers = (RegiocompetitieSporterBoog
                      .objects
                      .select_related('indiv_klasse',
                                      'bij_vereniging__regio',
                                      'sporterboog__sporter',
                                      'sporterboog__sporter__bij_vereniging',
                                      'sporterboog__sporter__bij_vereniging__regio__rayon')
                      .filter(regiocompetitie__in=pks,
                              aantal_scores__gte=competitie.aantal_scores_voor_rk_deelname,
                              indiv_klasse__is_ook_voor_rk_bk=True)     # skip aspiranten
                      .order_by('indiv_klasse__volgorde',               # groepeer per klasse
                                '-gemiddelde'))                         # aflopend gemiddelde

        # markeer de regiokampioenen
        klasse = -1
        regios = list()     # bijhouden welke kampioenen we al gemarkeerd hebben
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
                    kampioenen.sort()
                    for _, kampioen in kampioenen:
                        deelnemers.insert(insert_at, kampioen)
                        insert_at += 1
                        nr += 1
                    # for
                kampioenen = list()
                regios = list()
                insert_at = nr
                rank = 0

            # fake een paar velden uit KampioenschapSporterBoog
            rank += 1
            deelnemer.volgorde = rank
            deelnemer.deelname = DEELNAME_ONBEKEND

            scores = [deelnemer.score1, deelnemer.score2, deelnemer.score3, deelnemer.score4,
                      deelnemer.score5, deelnemer.score6, deelnemer.score7]
            scores.sort(reverse=True)      # beste score eerst
            deelnemer.regio_scores = "%03d%03d%03d%03d%03d%03d%03d" % tuple(scores)

            regio_nr = deelnemer.bij_vereniging.regio.regio_nr
            if regio_nr not in regios:
                regios.append(regio_nr)
                deelnemer.kampioen_label = "Kampioen regio %s" % regio_nr
                tup = (regio_nr, deelnemer)
                kampioenen.append(tup)
                deelnemers.pop(nr)
            else:
                # alle sporters overnemen als potentiële reserve-sporter
                deelnemer.kampioen_label = ""
                nr += 1
        # while

        if len(kampioenen):
            kampioenen.sort(reverse=True)       # hoogste regionummer bovenaan
            for _, kampioen in kampioenen:
                deelnemers.insert(insert_at, kampioen)
                insert_at += 1
            # for

        return deelnemers

    def _maak_deelnemerslijst_rks(self, comp):
        """ stel de deelnemerslijsten voor de kampioenschappen op
            aan de hand van gerechtigde deelnemers uit de regiocompetitie.
            ook wordt hier de vereniging van de sporter bevroren.
        """

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan de RK indiv deelnemerslijst\n" % stamp_str

        # sporters moeten in het rayon van hun huidige vereniging geplaatst worden
        rayon_nr2deelkamp = dict()
        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)):
            rayon_nr2deelkamp[deelkamp.rayon.rayon_nr] = deelkamp
        # for

        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)):

            deelnemers = self._get_regio_sporters_rayon(comp, deelkamp.rayon.rayon_nr)

            # schrijf all deze sporters in voor het RK
            # kampioenen als eerste in de lijst, daarna aflopend gesorteerd op gemiddelde
            bulk_lijst = list()
            for deelnemer in deelnemers:

                # sporter moet nu lid zijn bij een vereniging
                ver = deelnemer.sporterboog.sporter.bij_vereniging
                if ver:
                    # schrijf de sporter in het juiste rayon in
                    deelkamp = rayon_nr2deelkamp[ver.regio.rayon_nr]

                    kampioen = KampioenschapSporterBoog(
                                    kampioenschap=deelkamp,
                                    sporterboog=deelnemer.sporterboog,
                                    indiv_klasse=deelnemer.indiv_klasse,
                                    indiv_klasse_volgende_ronde=deelnemer.indiv_klasse,
                                    bij_vereniging=ver,             # bevries vereniging
                                    kampioen_label=deelnemer.kampioen_label,
                                    gemiddelde=deelnemer.gemiddelde,
                                    gemiddelde_scores=deelnemer.regio_scores,
                                    logboek=msg)

                    if not deelnemer.inschrijf_voorkeur_rk_bk:
                        # bij inschrijven al afgemeld voor RK/BK
                        kampioen.deelname = DEELNAME_NEE
                        kampioen.logboek += '[%s] Deelname op Nee gezet want geen voorkeur RK/BK' % stamp_str

                    bulk_lijst.append(kampioen)
                    if len(bulk_lijst) > 150:       # pragma: no cover
                        KampioenschapSporterBoog.objects.bulk_create(bulk_lijst)
                        bulk_lijst = list()
                else:
                    self.stdout.write(
                        '[WARNING] Sporter %s is geen RK deelnemer want heeft geen vereniging' % deelnemer.sporterboog)
            # for

            if len(bulk_lijst) > 0:
                KampioenschapSporterBoog.objects.bulk_create(bulk_lijst)
            del bulk_lijst
        # for

        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('rayon')
                         .filter(competitie=comp,
                                 deel=DEEL_RK)
                         .order_by('rayon__rayon_nr')):

            deelkamp.heeft_deelnemerslijst = True
            deelkamp.save(update_fields=['heeft_deelnemerslijst'])

            # laat de lijsten sorteren en de volgorde bepalen
            self.kamp_mutaties.verwerk_mutatie_initieel_deelkamp(deelkamp)

            # stuur de RKO een taak ('ter info')
            functie_rko = deelkamp.functie
            now = timezone.now()
            stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
            taak_deadline = now
            taak_onderwerp = "Deelnemerslijsten RK zijn vastgesteld"
            taak_tekst = "Ter info: De deelnemerslijsten voor jouw Rayonkampioenschappen zijn vastgesteld door de BKO"
            taak_log = "[%s] Taak aangemaakt" % stamp_str

            # maak een taak aan voor deze BKO
            maak_taak(toegekend_aan_functie=functie_rko,
                      deadline=taak_deadline,
                      aangemaakt_door=None,         # systeem
                      onderwerp=taak_onderwerp,
                      beschrijving=taak_tekst,
                      log=taak_log)

            # schrijf in het logboek
            msg = "De deelnemerslijst voor de Rayonkampioenschappen in %s is zojuist vastgesteld." % str(deelkamp.rayon)
            msg += '\nDe %s is geïnformeerd via een taak' % functie_rko
            schrijf_in_logboek(None, "Competitie", msg)
        # for

    def _converteer_rk_teams(self, comp):
        """ converteer de sporters die gekoppeld zijn aan de RK teams
            de RK teams zijn die tijdens de regiocompetitie al aangemaakt door de verenigingen
            en er zijn regiocompetitie sporters aan gekoppeld welke misschien niet gerechtigd zijn.

            controleer ook meteen de vereniging van de deelnemer
            als laatste wordt de team sterkte opnieuw berekend

            het vaststellen van de wedstrijdklasse voor de RK teams volgt later
        """

        # maak een look-up tabel van RegioCompetitieSporterBoog naar KampioenschapSporterBoog
        sporterboog_pk2regiocompetitiesporterboog = dict()
        for deelnemer in (RegiocompetitieSporterBoog
                          .objects
                          .select_related('bij_vereniging')
                          .filter(regiocompetitie__competitie=comp)):
            sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk] = deelnemer
        # for

        regiocompetitiesporterboog_pk2kampioenschapsporterboog = dict()
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .select_related('bij_vereniging')
                          .filter(kampioenschap__competitie=comp)):
            try:
                regio_deelnemer = sporterboog_pk2regiocompetitiesporterboog[deelnemer.sporterboog.pk]
            except KeyError:
                self.stdout.write(
                    '[WARNING] Kan regio deelnemer niet vinden voor kampioenschapsporterboog met pk=%s' %
                    deelnemer.pk)
            else:
                regiocompetitiesporterboog_pk2kampioenschapsporterboog[regio_deelnemer.pk] = deelnemer
        # for

        # sporters mogen maar aan 1 team gekoppeld worden
        gekoppelde_deelnemer_pks = list()

        for team in (KampioenschapTeam
                     .objects
                     .select_related('vereniging')
                     .prefetch_related('tijdelijke_leden')
                     .filter(kampioenschap__competitie=comp)):

            team_ver_nr = team.vereniging.ver_nr
            deelnemer_pks = list()

            ags = list()

            for pk in team.tijdelijke_leden.values_list('pk', flat=True):
                try:
                    deelnemer = regiocompetitiesporterboog_pk2kampioenschapsporterboog[pk]
                except KeyError:
                    # regio sporter is niet doorgekomen naar het RK en valt dus af
                    pass
                else:
                    # controleer de vereniging
                    if deelnemer.bij_vereniging.ver_nr == team_ver_nr:
                        # controleer dat de deelnemer nog niet aan een RK team gekoppeld is
                        if deelnemer.pk not in gekoppelde_deelnemer_pks:
                            gekoppelde_deelnemer_pks.append(deelnemer.pk)

                            deelnemer_pks.append(deelnemer.pk)
                            ags.append(deelnemer.gemiddelde)
            # for

            team.gekoppelde_leden.set(deelnemer_pks)

            # bepaal de team sterkte
            ags.sort(reverse=True)
            if len(ags) >= 3:
                team.aanvangsgemiddelde = sum(ags[:3])
            else:
                team.aanvangsgemiddelde = 0.0

            # de klasse wordt later bepaald als de klassengrenzen vastgesteld zijn
            team.team_klasse = None

            team.save(update_fields=['aanvangsgemiddelde', 'team_klasse'])
        # for

        # FUTURE: maak een taak aan voor de HWL's om de RK teams te herzien (eerst functionaliteit voor HWL maken)

    def verwerk_mutatie_regio_naar_rk(self, comp: Competitie):
        # let op: deze methode wordt aangeroepen vanuit VerwerktCompBeheerMutaties
        #         tijdens het afsluiten van de fase regiocompetities

        self.stdout.write('[INFO] {VerwerkCompLaagRayonMutaties} regio naar RK')

        # verwijder alle eerder aangemaakte KampioenschapSporterBoog
        # verwijder eerst alle eerder gekoppelde team leden
        for team in KampioenschapTeam.objects.filter(kampioenschap__competitie=comp):
            team.gekoppelde_leden.clear()
        # for
        KampioenschapSporterBoog.objects.filter(kampioenschap__competitie=comp).all().delete()

        # gerechtigde RK deelnemers aanmaken
        self._maak_deelnemerslijst_rks(comp)

        # RK teams opzetten en RK deelnemers koppelen
        self._converteer_rk_teams(comp)


# end of file
