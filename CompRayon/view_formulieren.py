# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import Http404, HttpResponse, FileResponse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import (CompetitieKlasse, LAAG_RK,
                               RegiocompetitieTeam, KampioenschapSchutterBoog, KampioenschapTeam)
from Competitie.menu import menu_dynamics_competitie
from Functie.rol import Rollen, rol_get_huidige_functie
from Wedstrijden.models import CompetitieWedstrijd
from tempfile import NamedTemporaryFile
import openpyxl
import shutil
import os


TEMPLATE_DOWNLOAD_RK_FORMULIER = 'comprayon/hwl-download-rk-formulier.dtl'


class DownloadRkFormulierView(UserPassesTestMixin, TemplateView):

    """ Toon de HWL of WL de waarschijnlijke deelnemerslijst voor een wedstrijd bij deze vereniging
    """

    # class variables shared by all instances
    template_name = TEMPLATE_DOWNLOAD_RK_FORMULIER
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('vereniging')
                         .prefetch_related('indiv_klassen',
                                           'team_klassen')
                         .get(pk=wedstrijd_pk))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp = plan.deelcompetitie_set.select_related('competitie', 'nhb_rayon').all()[0]
        if deelcomp.laag != LAAG_RK:
            raise Http404('Verkeerde competitie')

        comp = deelcomp.competitie
        # TODO: check fase
        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        if deelcomp.laag == LAAG_RK:
            wedstrijd.is_rk = True
            wedstrijd.beschrijving = "Rayonkampioenschap"
        # else:
        #     wedstrijd.is_bk = True
        #     wedstrijd.beschrijving = "Bondskampioenschap"

        heeft_indiv = heeft_teams = False
        beschr = list()

        klasse_indiv_pks = list()
        klasse_team_pks = list()
        wedstrijd.klassen_lijst = klassen_lijst = list()
        for klasse in wedstrijd.indiv_klassen.all():
            klassen_lijst.append(str(klasse))
            klasse_indiv_pks.append(klasse.pk)
            if not heeft_indiv:
                heeft_indiv = True
                beschr.append('Individueel')
        # for
        for klasse in wedstrijd.team_klassen.all():
            klassen_lijst.append(str(klasse))
            klasse_team_pks.append(klasse.pk)
            if not heeft_teams:
                heeft_teams = True
                beschr.append('Teams')
        # for

        context['deelcomp'] = deelcomp
        context['wedstrijd'] = wedstrijd
        context['vastgesteld'] = timezone.now()
        context['heeft_indiv'] = heeft_indiv
        context['heeft_teams'] = heeft_teams
        context['beschrijving'] = "%s %s" % (wedstrijd.beschrijving, " en ".join(beschr))

        # zoek de deelnemers erbij
        if heeft_indiv:
            deelnemers = (KampioenschapSchutterBoog
                          .objects
                          .filter(deelcompetitie=deelcomp,
                                  klasse__indiv__pk__in=klasse_indiv_pks)
                          .select_related('sporterboog',
                                          'sporterboog__sporter',
                                          'bij_vereniging',
                                          'klasse')
                          .order_by('klasse',
                                    'rank'))
            context['deelnemers_indiv'] = deelnemers

            prev_klasse = None
            for deelnemer in deelnemers:
                if deelnemer.klasse != prev_klasse:
                    deelnemer.break_before = True
                    deelnemer.url_download_indiv = reverse('CompRayon:formulier-indiv-als-bestand',
                                                           kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                                   'klasse_pk': deelnemer.klasse.pk})
                    prev_klasse = deelnemer.klasse

                deelnemer.ver_nr = deelnemer.bij_vereniging.ver_nr
                deelnemer.ver_naam = deelnemer.bij_vereniging.naam
                deelnemer.lid_nr = deelnemer.sporterboog.sporter.lid_nr
                deelnemer.volledige_naam = deelnemer.sporterboog.sporter.volledige_naam()
                deelnemer.gemiddelde_str = "%.3f" % deelnemer.gemiddelde
                deelnemer.gemiddelde_str = deelnemer.gemiddelde_str.replace('.', ',')
            # for

        if heeft_teams:
            teams = (KampioenschapTeam
                     .objects
                     .filter(deelcompetitie=deelcomp,
                             klasse__team__pk__in=klasse_team_pks)
                     .select_related('vereniging')
                     .prefetch_related('gekoppelde_schutters')
                     .all())
            context['deelnemers_teams'] = teams

            if not comp.klassengrenzen_vastgesteld_rk_bk:
                context['geen_klassengrenzen'] = True

            volg_nr = 0
            prev_klasse = None
            for team in teams:
                if team.klasse != prev_klasse:
                    team.break_before = True
                    team.url_download_teams = reverse('CompRayon:formulier-teams-als-bestand',
                                                      kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                              'klasse_pk': team.klasse.pk})

                    prev_klasse = team.klasse

                volg_nr += 1
                team.volg_nr = volg_nr
                team.ver_nr = team.vereniging.ver_nr
                team.ver_naam = team.vereniging.naam
                team.sterkte_str = "%.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
                team.sterkte_str = team.sterkte_str.replace('.', ',')

                for lid in team.gekoppelde_schutters.all():
                    sporter = lid.sporterboog.sporter
                    lid.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                    lid.gem_str = lid.gemiddelde
                # for
            # for

        menu_dynamics_competitie(self.request, context, comp_pk=comp.pk)
        return context


class FormulierIndivAlsBestandView(UserPassesTestMixin, TemplateView):

    """ Geef de HWL het ingevulde wedstrijdformulier voor een RK wedstrijd bij deze vereniging """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ Afhandelen van de GET request waarmee we een bestand terug geven. """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('vereniging')
                         .get(pk=wedstrijd_pk,
                              vereniging=self.functie_nu.nhb_ver))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        try:
            klasse_pk = int(kwargs['klasse_pk'][:6])            # afkappen voor de veiligheid
            klasse = (CompetitieKlasse
                      .objects
                      .exclude(indiv=None)
                      .get(pk=klasse_pk))
        except (ValueError, CompetitieKlasse.DoesNotExist):
            raise Http404('Klasse niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp = plan.deelcompetitie_set.select_related('competitie', 'nhb_rayon').all()[0]
        if deelcomp.laag != LAAG_RK:
            raise Http404('Verkeerde competitie')

        comp = deelcomp.competitie
        # TODO: check fase

        vastgesteld = timezone.now()

        klasse_str = klasse.indiv.beschrijving

        # bepaal de naam van het terug te geven bestand
        fname = "rk-programma_individueel-rayon%s_" % deelcomp.nhb_rayon.rayon_nr
        fname += klasse_str.lower().replace(' ', '-')
        fname += '.xlsm'

        # make een kopie van het RK programma in een tijdelijk bestand
        fpath = os.path.join(settings.INSTALL_PATH, 'CompRayon', 'files', 'template-excel-rk-indiv.xlsm')
        tmp_file = NamedTemporaryFile()
        shutil.copyfile(fpath, tmp_file.name)

        # open de kopie, zodat we die aan kunnen passen
        try:
            prg = openpyxl.open(tmp_file, keep_vba=True)
        except OSError:
            raise Http404('Kan RK programma niet openen')

        # maak wijzigingen in het RK programma
        ws = prg['Voorronde']

        ws['C4'] = 'Rayonkampioenschappen %s, Rayon %s, %s' % (comp.beschrijving, deelcomp.nhb_rayon.rayon_nr, klasse.indiv.beschrijving)

        deelnemers = (KampioenschapSchutterBoog
                      .objects
                      .filter(deelcompetitie=deelcomp,
                              klasse=klasse.pk)
                      .select_related('sporterboog',
                                      'sporterboog__sporter',
                                      'bij_vereniging',
                                      'bij_vereniging__regio',
                                      'klasse')
                      .order_by('klasse',
                                'rank'))

        row_nr = 6
        for deelnemer in deelnemers:
            row_nr += 1
            row = str(row_nr)

            # bondsnummer
            ws['D' + row] = deelnemer.sporterboog.sporter.lid_nr

            # volledige naam
            ws['E' + row] = deelnemer.sporterboog.sporter.volledige_naam()

            # vereniging
            ver = deelnemer.bij_vereniging
            ws['F' + row] = '%s %s' % (ver.ver_nr, ver.naam)

            # regio
            ws['G' + row] = ver.regio.regio_nr

            # klasse
            ws['H' + row] = klasse_str

            # gemiddelde
            ws['I' + row] = deelnemer.gemiddelde
        # for

        row_nr += 2
        ws['A' + str(row_nr)] = 'Deze gegevens zijn opgehaald op %s' % vastgesteld.strftime('%Y-%m-%d %H:%M:%S')

        # geef het aangepaste RK programma aan de client
        response = HttpResponse(content_type='application/vnd.ms-excel.sheet.macroEnabled.12')
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname
        prg.save(response)

        return response


class FormulierTeamsAlsBestandView(UserPassesTestMixin, TemplateView):

    """ Geef de HWL het ingevulde wedstrijdformulier voor een RK wedstrijd bij deze vereniging """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDefined als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu == Rollen.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ Afhandelen van de GET request waarmee we een bestand terug geven. """

        try:
            wedstrijd_pk = int(kwargs['wedstrijd_pk'][:6])      # afkappen voor de veiligheid
            wedstrijd = (CompetitieWedstrijd
                         .objects
                         .select_related('vereniging',
                                         'locatie')
                         .get(pk=wedstrijd_pk,
                              vereniging=self.functie_nu.nhb_ver))
        except (ValueError, CompetitieWedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        try:
            klasse_pk = int(kwargs['klasse_pk'][:6])            # afkappen voor de veiligheid
            klasse = (CompetitieKlasse
                      .objects
                      .exclude(team=None)
                      .get(pk=klasse_pk))
        except (ValueError, CompetitieKlasse.DoesNotExist):
            raise Http404('Klasse niet gevonden')

        plan = wedstrijd.competitiewedstrijdenplan_set.all()[0]
        deelcomp = plan.deelcompetitie_set.select_related('competitie', 'nhb_rayon').all()[0]
        if deelcomp.laag != LAAG_RK:
            raise Http404('Verkeerde competitie')

        comp = deelcomp.competitie
        # TODO: check fase

        if comp.afstand == '18':
            aantal_pijlen = 30
        else:
            aantal_pijlen = 25

        vastgesteld = timezone.now()

        klasse_str = klasse.team.beschrijving

        # bepaal de naam van het terug te geven bestand
        fname = "rk-programma_teams-rayon%s_" % deelcomp.nhb_rayon.rayon_nr
        fname += klasse_str.lower().replace(' ', '-')
        fname += '.xlsm'

        # make een kopie van het RK programma in een tijdelijk bestand
        fpath = os.path.join(settings.INSTALL_PATH, 'CompRayon', 'files', 'template-excel-rk-teams.xlsm')
        tmp_file = NamedTemporaryFile()
        shutil.copyfile(fpath, tmp_file.name)

        # open de kopie, zodat we die aan kunnen passen
        try:
            prg = openpyxl.open(tmp_file, keep_vba=True)
        except OSError:
            raise Http404('Kan RK programma niet openen')

        # maak wijzigingen in het RK programma
        ws = prg['scores']

        ws['B1'] = 'Rayonkampioenschappen Teams Rayon %s, %s' % (deelcomp.nhb_rayon.rayon_nr, comp.beschrijving)
        ws['B4'] = 'Klasse: ' + klasse_str
        ws['D3'] = wedstrijd.datum_wanneer.strftime('%Y-%m-%d')
        ws['E3'] = wedstrijd.vereniging.naam     # organisatie
        ws['H3'] = wedstrijd.locatie.adres       # adres van de wedstrijdlocatie

        teams = (KampioenschapTeam
                 .objects
                 .filter(deelcompetitie=deelcomp,
                         klasse=klasse.pk)
                 .select_related('vereniging',
                                 'vereniging__regio')
                 .prefetch_related('gekoppelde_schutters')
                 .order_by('aanvangsgemiddelde'))

        volg_nr = 0
        for team in teams:
            row_nr = 9 + volg_nr * 6
            row = str(row_nr)

            # regio
            ver = team.vereniging
            ws['C' + row] = ver.regio.regio_nr

            # vereniging
            ws['D' + row] = '[%s] %s' % (ver.ver_nr, ver.naam)

            # team naam
            ws['F' + row] = team.team_naam

            # team sterkte
            sterkte_str = "%.1f" % (team.aanvangsgemiddelde * aantal_pijlen)
            sterkte_str = sterkte_str.replace('.', ',')
            ws['G' + row] = sterkte_str

            # vul de 4 sporters in
            aantal = 0
            for deelnemer in team.gekoppelde_schutters.all():
                row_nr += 1
                row = str(row_nr)

                sporter = deelnemer.sporterboog.sporter

                # bondsnummer
                ws['E' + row] = sporter.lid_nr

                # volledige naam
                ws['F' + row] = sporter.volledige_naam()

                # regio gemiddelde
                ws['G' + row] = deelnemer.gemiddelde

                aantal += 1
            # for

            # bij minder dan 4 sporters de overgebleven regels leegmaken
            while aantal < 4:
                row_nr += 1
                row = str(row_nr)
                ws['E' + row] = '-'         # bondsnummer
                ws['F' + row] = 'n.v.t.'    # naam
                ws['G' + row] = ''          # gemiddelde
                ws['H' + row] = ''          # score 1
                ws['I' + row] = ''          # score 2
                aantal += 1
            # while

            volg_nr += 1
        # for

        while volg_nr < 12:
            row_nr = 9 + volg_nr * 6
            row = str(row_nr)

            # vereniging leeg maken
            ws['C' + row] = '-'          # regio
            ws['D' + row] = 'n.v.t.'     # vereniging
            ws['F' + row] = 'n.v.t.'     # team naam
            ws['G' + row] = ''           # team sterkte

            # sporters leegmaken
            aantal = 0
            while aantal < 4:
                row_nr += 1
                row = str(row_nr)
                ws['E' + row] = '-'         # bondsnummer
                ws['F' + row] = '-'         # naam
                ws['G' + row] = ''          # gemiddelde
                ws['H' + row] = ''          # score 1
                ws['I' + row] = ''          # score 2
                aantal += 1
            # while

            volg_nr += 1
        # while

        ws['B82'] = 'Deze gegevens zijn opgehaald op %s' % vastgesteld.strftime('%Y-%m-%d %H:%M:%S')

        # TODO: all invallers opnemen op een apart tabblad, met gemiddelde

        # geef het aangepaste RK programma aan de client
        response = HttpResponse(content_type='application/vnd.ms-excel.sheet.macroEnabled.12')
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname
        prg.save(response)

        return response


# end of file
