# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.db.models import Count
from django.utils.http import urlencode
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Competitie.models import CompetitieMatch
from Account.models import get_account
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige, rol_get_huidige_functie, gebruiker_is_scheids
from Locatie.models import Reistijd
from Scheidsrechter.definities import SCHEIDS2LEVEL, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE, BESCHIKBAAR_JA
from Scheidsrechter.models import MatchScheidsrechters, ScheidsBeschikbaarheid
from Scheidsrechter.mutaties import scheids_mutatieverzoek_stuur_notificaties_match
from Scheidsrechter.operations import get_bezette_scheidsrechters
from Sporter.models import SporterVoorkeuren
from Wedstrijden.models import Wedstrijd
from types import SimpleNamespace
import datetime

TEMPLATE_MATCHES = 'scheidsrechter/matches.dtl'
TEMPLATE_MATCH_DETAILS = 'scheidsrechter/match-details.dtl'
TEMPLATE_MATCH_CS_KIES_SR = 'scheidsrechter/match-cs-kies-sr.dtl'
TEMPLATE_WEDSTRIJD_HWL_CONTACT = 'scheidsrechter/match-hwl-contact.dtl'


class CompetitieMatchesView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_MATCHES
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_cs = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rol.ROL_CS:
            self.is_cs = True
            return True
        if rol_nu == Rol.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    @staticmethod
    def _check_beschikbaarheid_opvragen():
        dit_jaar = timezone.make_aware(datetime.datetime(year=timezone.now().year, month=1, day=1))

        alle_rk_datums = list()
        alle_bk_datums = list()
        alle_match_pks = list()

        een_match = None

        for match in (CompetitieMatch
                      .objects
                      .filter(datum_wanneer__gte=dit_jaar,
                              aantal_scheids__gte=1,
                              competitie__afstand=18)   # Indoor
                      .order_by('datum_wanneer',        # oudste bovenaan
                                'beschrijving')):       # ivm veel dezelfde datum

            alle_match_pks.append(match.pk)
            een_match = match
            if match.beschrijving.startswith('BK'):
                if match.datum_wanneer not in alle_bk_datums:
                    alle_bk_datums.append(match.datum_wanneer)
            else:
                if match.datum_wanneer not in alle_rk_datums:
                    alle_rk_datums.append(match.datum_wanneer)
        # for

        if not een_match:
            # geen matches, dus niets op te vragen
            return False

        pos = een_match.beschrijving.find(', ')
        titel = ' wedstrijden' + een_match.beschrijving[pos:]

        qset = (MatchScheidsrechters
                .objects
                .filter(match__in=alle_match_pks))

        if qset.count() < len(alle_match_pks):
            # er moet nog wat bij
            return True

        if len(alle_rk_datums) > 0:
            rk_titel = 'RK' + titel
            try:
                rk_wedstrijd = Wedstrijd.objects.get(titel=rk_titel,
                                                     toon_op_kalender=False, verstop_voor_mwz=True,
                                                     datum_begin__gt=dit_jaar)
            except Wedstrijd.DoesNotExist:
                # geen wedstrijd, dus we moeten nog opvragen
                return True

            for datum in alle_rk_datums:
                if not (rk_wedstrijd.datum_begin <= datum <= rk_wedstrijd.datum_einde):
                    # reeks moet uitgebreid worden
                    return True
            # for

        if len(alle_bk_datums) > 0:
            bk_titel = 'BK' + titel
            try:
                bk_wedstrijd = Wedstrijd.objects.get(titel=bk_titel,
                                                     toon_op_kalender=False, verstop_voor_mwz=True,
                                                     datum_begin=alle_bk_datums[0])
            except Wedstrijd.DoesNotExist:
                # geen wedstrijd, dus we moeten nog opvragen
                return True

            for datum in alle_bk_datums:
                if not (bk_wedstrijd.datum_begin <= datum <= bk_wedstrijd.datum_einde):
                    # reeks moet uitgebreid worden
                    return True
            # for

        # ziek er compleet uit
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vandaag = timezone.now().date()
        vorige_week = vandaag - datetime.timedelta(days=7)

        context['matches'] = matches = list()
        context['is_cs'] = self.is_cs

        for match in (CompetitieMatch
                      .objects
                      .filter(datum_wanneer__gte=vorige_week,
                              competitie__afstand=18,       # Indoor
                              aantal_scheids__gte=1)
                      .annotate(aantal_klassen_team=Count('team_klassen'),
                                aantal_klassen_indiv=Count('indiv_klassen'))
                      .order_by('datum_wanneer',       # oudste bovenaan
                                'beschrijving')):      # ivm veel dezelfde datum

            match.aantal_str = str(match.aantal_scheids)

            match.mag_wijzigen = self.is_cs and match.datum_wanneer >= vandaag

            indiv_team = []
            if match.aantal_klassen_indiv > 0:
                indiv_team.append('Individueel')
            if match.aantal_klassen_team > 0:
                indiv_team.append('Team')
            match.indiv_team_str = " en ".join(indiv_team)

            if self.is_cs:
                match.url_details = reverse('Scheidsrechter:match-kies-scheidsrechter',
                                            kwargs={'match_pk': match.pk})
            else:
                match.url_details = reverse('Scheidsrechter:match-details',
                                            kwargs={'match_pk': match.pk})

            matches.append(match)
        # for

        if self.is_cs:
            # kijk of de beschikbaarheid van het RK of BK nog opgevraagd moet worden
            if self._check_beschikbaarheid_opvragen():
                context['url_opvragen'] = reverse('Scheidsrechter:competitie-beschikbaarheid-opvragen')

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Bondscompetitie')
        )

        return context


class MatchDetailsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_MATCH_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rol.ROL_SPORTER and gebruiker_is_scheids(self.request)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            match_pk = str(kwargs['match_pk'])[:6]     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .filter(competitie__afstand=18)
                     .exclude(vereniging=None)
                     .select_related('vereniging',
                                     'locatie')
                     .prefetch_related('indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except CompetitieMatch.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['match'] = match

        toon_kaart = match.locatie.plaats != '(diverse)' and match.locatie.adres != '(diverse)'
        if toon_kaart:          # pragma: no branch
            zoekterm = match.locatie.adres
            if match.locatie.adres_uit_crm:
                # voeg de naam van de vereniging toe aan de zoekterm, voor beter resultaat
                zoekterm = match.vereniging.naam + ' ' + zoekterm
            zoekterm = zoekterm.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
            context['url_map'] = 'https://google.nl/maps?' + urlencode({'q': zoekterm})

        # contactgegevens van de HWL
        match.contact_naam = ''
        match.contact_telefoon = ''
        match.contact_email = ''
        functie_hwl = (Functie
                       .objects
                       .prefetch_related('accounts')
                       .filter(vereniging=match.vereniging,
                               rol='HWL')
                       .first())
        if functie_hwl:
            eerste_hwl = functie_hwl.accounts.first()
            if eerste_hwl:
                match.contact_naam = eerste_hwl.volledige_naam()
            match.contact_telefoon = functie_hwl.telefoon
            match.contact_email = functie_hwl.bevestigde_email

        match.klassen = list()
        for klasse in match.indiv_klassen.order_by('volgorde'):
            match.klassen.append(klasse.beschrijving)
        # for
        for klasse in match.team_klassen.order_by('volgorde'):
            match.klassen.append(klasse.beschrijving)
        # for

        try:
            match_sr = (MatchScheidsrechters
                        .objects
                        .select_related('gekozen_hoofd_sr',
                                        'gekozen_sr1',
                                        'gekozen_sr2')
                        .get(match=match))
        except MatchScheidsrechters.DoesNotExist:
            # nog niet aangemaakt
            pass
        else:
            match.gekozen = list()
            for sr in (match_sr.gekozen_hoofd_sr, match_sr.gekozen_sr1, match_sr.gekozen_sr2):
                if sr:
                    level_naam_str = '%s: %s' % (SCHEIDS2LEVEL[sr.scheids], sr.volledige_naam())
                    match.gekozen.append(level_naam_str)
            # for

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:competitie'), 'Bondscompetitie'),
            (None, 'Details'),
        )

        return context


class MatchDetailsCSView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_MATCH_CS_KIES_SR
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu == Rol.ROL_CS

    @staticmethod
    def _vind_wedstrijd(match):
        dit_jaar = timezone.make_aware(datetime.datetime(year=timezone.now().year, month=1, day=1))

        pos = match.beschrijving.find(', ')
        titel = ' wedstrijden' + match.beschrijving[pos:]

        for titel in ('RK' + titel, 'BK' + titel):
            wedstrijd = (Wedstrijd
                         .objects
                         .filter(titel=titel,
                                 toon_op_kalender=False, verstop_voor_mwz=True,
                                 datum_begin__gt=dit_jaar)
                         .select_related('locatie')
                         .first())

            if wedstrijd:
                # kijk of de wedstrijddatum past in deze wedstrijd
                if wedstrijd.datum_begin <= match.datum_wanneer <= wedstrijd.datum_einde:
                    return wedstrijd
        # for

        return None

    @staticmethod
    def _get_alle_sr_reistijd(locatie):
        reistijd_min = dict()  # [(adres_lat, adres_lon)] = reistijd in minuten
        for reistijd in Reistijd.objects.filter(naar_lat=locatie.adres_lat, naar_lon=locatie.adres_lon):
            reistijd_min[(reistijd.vanaf_lat, reistijd.vanaf_lon)] = reistijd.reistijd_min
        # for
        return reistijd_min

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            match_pk = str(kwargs['match_pk'])[:6]     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .filter(competitie__afstand=18)
                     .exclude(vereniging=None)
                     .select_related('vereniging',
                                     'locatie')
                     .prefetch_related('indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except CompetitieMatch.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['match'] = match

        if match.locatie:
            toon_kaart = match.locatie.plaats != '(diverse)' and match.locatie.adres != '(diverse)'
            if toon_kaart:              # pragma: no branch
                zoekterm = match.locatie.adres
                if match.locatie.adres_uit_crm:
                    # voeg de naam van de vereniging toe aan de zoekterm, voor beter resultaat
                    zoekterm = match.vereniging.naam + ' ' + zoekterm
                zoekterm = zoekterm.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
                context['url_map'] = 'https://google.nl/maps?' + urlencode({'q': zoekterm})

        # contactgegevens van de HWL
        match.contact_naam = ''
        match.contact_telefoon = ''
        match.contact_email = ''
        functie_hwl = (Functie
                       .objects
                       .prefetch_related('accounts')
                       .filter(vereniging=match.vereniging,
                               rol='HWL')
                       .first())
        if functie_hwl:
            eerste_hwl = functie_hwl.accounts.first()
            if eerste_hwl:
                match.contact_naam = eerste_hwl.volledige_naam()
            match.contact_telefoon = functie_hwl.telefoon
            match.contact_email = functie_hwl.bevestigde_email

        match.klassen = list()
        for klasse in match.indiv_klassen.order_by('volgorde'):
            match.klassen.append(klasse.beschrijving)
        # for
        for klasse in match.team_klassen.order_by('volgorde'):
            match.klassen.append(klasse.beschrijving)
        # for

        # zoek de RK/BK wedstrijd erbij
        rk_bk_wedstrijd = self._vind_wedstrijd(match)

        # zoek de reistijden erbij
        reistijd_min = dict()
        if match.locatie:
            reistijd_min = self._get_alle_sr_reistijd(match.locatie)

        context['keuze_aantal_scheids'] = [
            # (0, 'Geen scheidsrechters'),
            (1, '1 scheidsrechter'),
            (2, '2 scheidsrechters'),
            (3, '3 scheidsrechters'),
        ]

        context['url_wijzigen'] = reverse('Scheidsrechter:match-kies-scheidsrechter',
                                          kwargs={'match_pk': match.pk})

        context['aantal_additionele_sr'] = match.aantal_scheids - 1

        try:
            match_sr = (MatchScheidsrechters
                        .objects
                        .select_related('gekozen_hoofd_sr',
                                        'gekozen_sr1',
                                        'gekozen_sr2')
                        .get(match=match))
        except MatchScheidsrechters.DoesNotExist:
            # nog niet aangemaakt
            pass
        else:
            context['match_sr'] = match_sr

            for sr in (match_sr.gekozen_hoofd_sr, match_sr.gekozen_sr1, match_sr.gekozen_sr2):
                if sr:
                    sr.level_naam_str = '%s: %s' % (SCHEIDS2LEVEL[sr.scheids], sr.volledige_naam())
            # for

            bezette_srs = get_bezette_scheidsrechters(match.datum_wanneer, ignore_match=match)

            beschikbaar_hsr = list()
            beschikbaar_sr = list()
            bevat_fouten = False

            geen_hsr = SimpleNamespace(
                                pk='geen',
                                scheids=None,
                                is_selected=match_sr.gekozen_hoofd_sr is None,
                                id_li='id_hsr_geen',
                                is_onzeker=False,
                                sel='geen')
            beschikbaar_hsr.append(geen_hsr)

            # voeg de beschikbare hoofdscheidsrechter toe (mag ook SR3 zijn)
            hsr_nog_beschikbaar = False
            for beschikbaar in (ScheidsBeschikbaarheid
                                .objects
                                .filter(wedstrijd=rk_bk_wedstrijd,
                                        datum=match.datum_wanneer,
                                        opgaaf=BESCHIKBAAR_JA)
                                .select_related('scheids')
                                .order_by('scheids__voornaam',
                                          'scheids__achternaam',
                                          'scheids__lid_nr')):

                beschikbaar.id_li = 'id_hsr_%s' % beschikbaar.pk
                # beschikbaar.is_onzeker = (beschikbaar.opgaaf == BESCHIKBAAR_DENK)
                beschikbaar.is_selected = (match_sr.gekozen_hoofd_sr == beschikbaar.scheids)
                hsr_nog_beschikbaar |= (match_sr.gekozen_hoofd_sr == beschikbaar.scheids)

                beschikbaar.level_naam_str = "%s: %s" % (SCHEIDS2LEVEL[beschikbaar.scheids.scheids],
                                                         beschikbaar.scheids.volledige_naam())

                if beschikbaar.scheids.lid_nr in bezette_srs:
                    beschikbaar.is_onzeker = True
                    beschikbaar.level_naam_str += ' [bezet]'
                else:
                    # voeg reistijd toe
                    scheids = beschikbaar.scheids
                    try:
                        mins = reistijd_min[(scheids.adres_lat, scheids.adres_lon)]
                    except KeyError:
                        mins = '??'
                    beschikbaar.level_naam_str += ' (reistijd %s min)' % mins

                beschikbaar_hsr.append(beschikbaar)
            # for

            if not hsr_nog_beschikbaar and match_sr.gekozen_hoofd_sr:
                # gekozen hoofdscheidsrechter is niet meer beschikbaar
                bevat_fouten = True
                niet_meer_hsr = SimpleNamespace(
                                    pk=0,       # wordt gebruikt als value
                                    id_li='id_hsr_niet_%s' % match_sr.gekozen_hoofd_sr.pk,
                                    scheids=match_sr.gekozen_hoofd_sr,
                                    is_selected=True,
                                    waarschuw_niet_meer_beschikbaar=True,
                                    level_naam_str="%s: %s" % (SCHEIDS2LEVEL[match_sr.gekozen_hoofd_sr.scheids],
                                                               match_sr.gekozen_hoofd_sr.volledige_naam()))
                beschikbaar_hsr.insert(1, niet_meer_hsr)

            gekozen_srs = [gekozen_sr.pk
                           for gekozen_sr in (match_sr.gekozen_sr1, match_sr.gekozen_sr2)
                           if gekozen_sr is not None]

            toon_additionele_sr = False
            if len(gekozen_srs) > 0 or match.aantal_scheids > 1:
                toon_additionele_sr = True

                # haal de beschikbare scheidsrechters op
                for beschikbaar in (ScheidsBeschikbaarheid
                                    .objects
                                    .filter(wedstrijd=rk_bk_wedstrijd,
                                            datum=match.datum_wanneer)
                                    .exclude(opgaaf=BESCHIKBAAR_NEE)
                                    .select_related('scheids')
                                    .order_by('scheids__voornaam', 'scheids__achternaam', 'scheids__lid_nr')):

                    beschikbaar.id_li = 'id_sr_%s' % beschikbaar.pk
                    beschikbaar.sel = 'sr_%s' % beschikbaar.pk
                    beschikbaar.is_onzeker = (beschikbaar.opgaaf == BESCHIKBAAR_DENK)
                    if beschikbaar.scheids.pk in gekozen_srs:
                        beschikbaar.is_selected = True
                        gekozen_srs.remove(beschikbaar.scheids.pk)
                    else:
                        beschikbaar.is_selected = False

                    beschikbaar.waarschuw_niet_meer_beschikbaar = (beschikbaar.is_selected and
                                                                   beschikbaar.opgaaf != BESCHIKBAAR_JA)
                    if beschikbaar.waarschuw_niet_meer_beschikbaar:
                        bevat_fouten = True
                        beschikbaar.is_onzeker = False  # voorkom disable van checkbox

                    beschikbaar.level_naam_str = "%s: %s" % (SCHEIDS2LEVEL[beschikbaar.scheids.scheids],
                                                             beschikbaar.scheids.volledige_naam())

                    if beschikbaar.scheids.lid_nr in bezette_srs:
                        beschikbaar.is_onzeker = True
                        beschikbaar.level_naam_str += ' [bezet]'
                    else:
                        if beschikbaar.is_onzeker:
                            beschikbaar.level_naam_str += ' [overweegt]'

                    beschikbaar_sr.append(beschikbaar)
                # for

                # kijk welke scheidsrechters nog over zijn en dus niet meer kunnen
                for gekozen_sr in (match_sr.gekozen_sr1, match_sr.gekozen_sr2):

                    if gekozen_sr and gekozen_sr.pk in gekozen_srs:
                        niet_meer_sr = SimpleNamespace(
                                        id_li='id_sr_niet_%s' % gekozen_sr.pk,
                                        sel='sr_niet_%s' % gekozen_sr.pk,
                                        scheids=gekozen_sr,
                                        is_selected=True,
                                        waarschuw_niet_meer_beschikbaar=True,
                                        level_naam_str="%s: %s" % (SCHEIDS2LEVEL[gekozen_sr.scheids],
                                                                   gekozen_sr.volledige_naam()))
                        beschikbaar_sr.insert(0, niet_meer_sr)
                        bevat_fouten = True
                # for

            if len(beschikbaar_hsr) == 1:
                # alleen de optie "nog niet gekozen" is beschikbaar
                # voorkom dat de knop "Stuur notificatie emails" getoond wordt
                bevat_fouten = True

            notified_lijst = [sr for sr in match_sr.notified_srs.order_by('lid_nr')]

            context['notify_last'] = match_sr.notified_laatste

            match_sr.nr_hsr = "hsr"
            match_sr.beschikbaar_hoofd_sr = beschikbaar_hsr
            match_sr.beschikbaar_sr = beschikbaar_sr
            match_sr.bevat_fouten = bevat_fouten
            match_sr.toon_additionele_sr = toon_additionele_sr
            match_sr.notified_wie = notified_lijst

            if bevat_fouten:
                context['url_notify'] = None
            else:
                context['url_notify'] = context['url_wijzigen']

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:competitie'), 'Bondscompetitie'),
            (None, 'Kies scheidsrechters'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        # print('POST: %s' % repr(list(request.POST.items())))

        try:
            match_pk = str(kwargs['match_pk'])[:6]     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .filter(competitie__afstand=18)
                     .exclude(vereniging=None)
                     .select_related('vereniging',
                                     'locatie')
                     .prefetch_related('indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except CompetitieMatch.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        # aantal scheidsrechters
        aantal_scheids_str = request.POST.get('aantal_scheids', '')
        try:
            aantal_scheids = int(aantal_scheids_str[:3])  # afkappen voor de veiligheid
        except ValueError:
            # no change
            pass
        else:
            if 1 <= aantal_scheids <= 3:
                if match.aantal_scheids != aantal_scheids:
                    match.aantal_scheids = aantal_scheids
                    match.save(update_fields=['aantal_scheids'])

        try:
            match_sr = (MatchScheidsrechters
                        .objects
                        .select_related('gekozen_hoofd_sr',
                                        'gekozen_sr1',
                                        'gekozen_sr2')
                        .get(match=match))
        except MatchScheidsrechters.DoesNotExist:
            # nog niet aangemaakt
            pass
        else:
            # zoek de RK/BK wedstrijd erbij (beschikbaarheid SR is hieraan gekoppeld)
            rk_bk_wedstrijd = self._vind_wedstrijd(match)
            if rk_bk_wedstrijd:
                # SR koppelen
                nr_hsr = "hsr"
                gekozen = request.POST.get(nr_hsr, '')
                gekozen = str(gekozen)[:6]      # afkappen voor de veiligheid
                if gekozen:
                    if gekozen == 'geen':
                        match_sr.gekozen_hoofd_sr = None
                    else:
                        try:
                            pk = int(gekozen)
                            beschikbaar = (ScheidsBeschikbaarheid
                                           .objects
                                           .filter(wedstrijd=rk_bk_wedstrijd,
                                                   datum=match.datum_wanneer,
                                                   opgaaf=BESCHIKBAAR_JA)           # exclude NEE en DENK
                                           .select_related('scheids')
                                           .get(pk=pk))
                        except (ValueError, ScheidsBeschikbaarheid.DoesNotExist):
                            raise Http404('Slechte parameter (1)')

                        match_sr.gekozen_hoofd_sr = beschikbaar.scheids

                # kijk welke scheidsrechters gekozen zijn
                gekozen_srs = list()
                for beschikbaar in (ScheidsBeschikbaarheid
                                    .objects
                                    .filter(wedstrijd=rk_bk_wedstrijd,
                                            datum=match.datum_wanneer)
                                    .filter(opgaaf=BESCHIKBAAR_JA)      # exclude NEE en DENK
                                    .select_related('scheids')):

                    sel = 'sr_%s' % beschikbaar.pk
                    gekozen = request.POST.get(sel, '')
                    if gekozen:
                        if match_sr.gekozen_hoofd_sr != beschikbaar.scheids:
                            gekozen_srs.append(beschikbaar.scheids)
                # for

                # zorg dat er minimaal 2 entries in de lijst staan
                gekozen_srs.extend([None]*2)

                match_sr.gekozen_sr1 = gekozen_srs[0]
                match_sr.gekozen_sr2 = gekozen_srs[1]

                match_sr.save(update_fields=['gekozen_hoofd_sr', 'gekozen_sr1', 'gekozen_sr2'])

        # notificatie
        do_notify = str(request.POST.get('notify', ''))[:1] == 'J'
        if do_notify:
            account = get_account(request)
            door_str = "CS %s" % account.volledige_naam()
            door_str = door_str[:149]

            snel = str(request.POST.get('snel', ''))[:1]

            scheids_mutatieverzoek_stuur_notificaties_match(match, door_str, snel == '1')

        url = reverse('Scheidsrechter:competitie')
        return HttpResponseRedirect(url)


class MatchHWLContactView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJD_HWL_CONTACT
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            match_pk = str(kwargs['match_pk'])[:6]     # afkappen voor de veiligheid
            match = (CompetitieMatch
                     .objects
                     .filter(competitie__afstand=18)
                     .exclude(vereniging=None)
                     .select_related('vereniging',
                                     'locatie')
                     .prefetch_related('indiv_klassen',
                                       'team_klassen')
                     .get(pk=match_pk))
        except CompetitieMatch.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if match.vereniging != self.functie_nu.vereniging:
            raise Http404('Verkeerde beheerder')

        context['match'] = match
        context['vereniging'] = match.vereniging
        context['locatie'] = match.locatie

        if match.aantal_scheids > 0:
            match_sr = MatchScheidsrechters.objects.filter(match=match).first()
            if match_sr:
                srs_pks = [sr.pk for sr in match_sr.notified_srs.all()]

                sr2voorkeur = dict()
                for voorkeur in SporterVoorkeuren.objects.filter(sporter__pk__in=srs_pks):
                    sr2voorkeur[voorkeur.sporter.pk] = (voorkeur.scheids_opt_in_ver_tel_nr,
                                                        voorkeur.scheids_opt_in_ver_email)
                # for

                sr = match_sr.gekozen_hoofd_sr
                if sr and sr.pk in srs_pks:
                    context['hoofd_sr_naam'] = sr.volledige_naam()

                context['srs'] = srs = list()
                for sr in match_sr.notified_srs.all():
                    sr.give_tel_nr, sr.give_email = sr2voorkeur[sr.pk]
                    tup = (sr.lid_nr, sr)
                    srs.append(tup)
                # for
                srs.sort()
            # for

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('CompScores:wedstrijden'), 'Competitie wedstrijden'),
            (None, 'Scheidsrechters')
        )

        return context


# end of file
