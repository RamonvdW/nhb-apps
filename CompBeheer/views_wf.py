# -*- coding: utf-8 -*-
#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEEL_BK
from Competitie.models import Competitie, CompetitieMatch, Kampioenschap
from CompKampioenschap.models import SheetStatus
from CompKampioenschap.operations import (maak_mutatie_wedstrijdformulieren_aanmaken,
                                          aantal_ontbrekende_wedstrijdformulieren_rk_bk)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from GoogleDrive.models import Bestand
from GoogleDrive.operations import check_heeft_toestemming, get_authorization_url

TEMPLATE_COMPBEHEER_DRIVE_TOESTEMMING = 'compbeheer/drive-toestemming.dtl'
TEMPLATE_COMPBEHEER_DRIVE_AANMAKEN = 'compbeheer/drive-aanmaken.dtl'
TEMPLATE_COMPBEHEER_WF_STATUS = 'compbeheer/wf-status.dtl'


class ToestemmingView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om toestemming te geven tot een Google Drive """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DRIVE_TOESTEMMING
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # kijk of de toestemming er al is
        if check_heeft_toestemming():
            context['heeft_toestemming'] = True
        else:
            context['url_toestemming'] = reverse('CompBeheer:wf-toestemming-drive')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Toestemming Google Drive'),
        )

        return context

    @staticmethod
    def post(request, *args, **kwargs):

        account = get_account(request)
        url = get_authorization_url(account.username, account.bevestigde_email)

        # stuur de gebruiker door naar Google
        return HttpResponseRedirect(url)


class AanmakenView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om het aanmaken van de formulieren op te starten """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_DRIVE_AANMAKEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def _get_begin_jaar_or_404(self):
        comp = Competitie.objects.order_by('begin_jaar').first()
        if not comp:
            raise Http404('Geen competitie gevonden')

        return comp.begin_jaar

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # kijk of de toestemming er al is
        if not check_heeft_toestemming():
            raise Http404('Geen toestemming')

        begin_jaar = self._get_begin_jaar_or_404()

        comp18 = Competitie.objects.filter(begin_jaar=begin_jaar, afstand=18).first()
        context['aantal_aanmaken_18'] = aantal_ontbrekende_wedstrijdformulieren_rk_bk(comp18)

        comp25 = Competitie.objects.filter(begin_jaar=begin_jaar, afstand=25).first()
        context['aantal_aanmaken_25'] = aantal_ontbrekende_wedstrijdformulieren_rk_bk(comp25)

        context['url_aanmaken'] = reverse('CompBeheer:wf-aanmaken')

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Aanmaken wedstrijdformulieren'),
        )

        return context

    def post(self, request, *args, **kwargs):
        # gebruiker heeft op de knop BEGIN gedrukt
        # het form heeft een POST gedaan, welke hier uit komt

        account = get_account(request)
        door_str = account.get_account_full_name()

        begin_jaar = self._get_begin_jaar_or_404()

        comp18 = Competitie.objects.filter(begin_jaar=begin_jaar, afstand=18).first()
        if comp18:
            maak_mutatie_wedstrijdformulieren_aanmaken(comp18, door_str)

        comp25 = Competitie.objects.filter(begin_jaar=begin_jaar, afstand=25).first()
        if comp25:
            maak_mutatie_wedstrijdformulieren_aanmaken(comp25, door_str)

        return HttpResponseRedirect(reverse('Competitie:kies'))


class StatusView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de manager om het de status van de wedstrijdformulieren te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBEHEER_WF_STATUS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_BB

    def _get_werk(self):
        werk = list()
        for comp in Competitie.objects.all():
            comp.bepaal_fase()

            is_teams = False
            if 'J' <= comp.fase_indiv <= 'L':
                is_bk = False
                tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                werk.append(tup)

            if 'N' <= comp.fase_indiv <= 'P':
                is_bk = True
                tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                werk.append(tup)

            if False:  # teams are Excel, for now
                is_teams = True
                if 'J' <= comp.fase_teams <= 'L':
                    is_bk = False
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

                if 'N' <= comp.fase_teams <= 'P':
                    is_bk = True
                    tup = (comp.begin_jaar, int(comp.afstand), is_bk, is_teams)
                    werk.append(tup)

        # for
        return werk

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        werk = self._get_werk()

        match_pk2deelkamp = dict()
        for deelkamp in (Kampioenschap
                         .objects
                         .select_related('competitie',
                                         'rayon')
                         .prefetch_related('rk_bk_matches')):

            match_pks = list(deelkamp.rk_bk_matches.all().values_list('pk', flat=True))
            for pk in match_pks:
                match_pk2deelkamp[pk] = deelkamp
            # for
        # for
        all_match_pks = list(match_pk2deelkamp.keys())

        tup2status = dict()
        for status in (SheetStatus
                       .objects
                       .select_related('bestand')
                       .order_by('bestand__fname')):

            bestand = status.bestand
            tup = (bestand.begin_jaar, bestand.afstand, bestand.is_bk, bestand.is_teams)
            if tup[:4] in werk:
                status.url_open_wf = "https://docs.google.com/spreadsheets/d/%s/edit" % status.bestand.file_id

                pos = status.gewijzigd_door.find('@')
                if pos > 0:
                    status.gewijzigd_door = status.gewijzigd_door[:pos]

                # improve wbr
                status.bestand.fname = status.bestand.fname.replace('_', ' ')
                status.bestand.fname = status.bestand.fname.replace('individueel-', 'individueel ')
                status.bestand.fname = status.bestand.fname.replace('-onder', ' onder')
                status.bestand.fname = status.bestand.fname.replace('-jeugd', ' jeugd')
                status.bestand.fname = status.bestand.fname.replace('-klasse', ' klasse')

                tup = (bestand.begin_jaar, bestand.afstand, bestand.is_bk, bestand.is_teams, bestand.rayon_nr, bestand.klasse_pk)
                tup2status[tup] = status
        # for

        context['matches'] = matches = list()

        prev_datum = None
        for match in (CompetitieMatch
                      .objects
                      .filter(pk__in=all_match_pks)
                      .select_related('vereniging')
                      .prefetch_related('indiv_klassen',
                                        'team_klassen')
                      .order_by('datum_wanneer',
                                'vereniging__regio__rayon_nr',
                                'vereniging__ver_nr')):

            deelkamp = match_pk2deelkamp[match.pk]
            comp = deelkamp.competitie
            afstand = int(comp.afstand)
            is_bk = deelkamp.deel == DEEL_BK
            if is_bk:
                rayon_nr = 0
            else:
                rayon_nr = deelkamp.rayon.rayon_nr

            match.status_list = list()

            for klasse in match.indiv_klassen.all():
                tup = (comp.begin_jaar, afstand, is_bk, False, rayon_nr, klasse.pk)
                status = tup2status.get(tup, None)
                if status:
                    match.status_list.append(status)
            # for

            for klasse in match.team_klassen.all():
                tup = (comp.begin_jaar, afstand, is_bk, True, rayon_nr, klasse.pk)
                status = tup2status.get(tup, None)
                if status:
                    match.status_list.append(status)
            # for

            if len(match.status_list) > 0:
                if prev_datum != match.datum_wanneer:
                    match.do_header = True
                    prev_datum = match.datum_wanneer

                matches.append(match)
        # for

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Status wedstrijdformulieren'),
        )

        return context



# end of file
