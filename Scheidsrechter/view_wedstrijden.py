# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import ORGANISATIE_IFAA
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Scheidsrechter.definities import SCHEIDS_VERENIGING, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE, BESCHIKBAAR_JA
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid
from Scheidsrechter.mutaties import scheids_mutatieverzoek_stuur_notificaties
from Wedstrijden.definities import (WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_ORGANISATIE_TO_STR,
                                    ORGANISATIE_WA, WEDSTRIJD_WA_STATUS_TO_STR,
                                    WEDSTRIJD_BEGRENZING_TO_STR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
from types import SimpleNamespace
import datetime

TEMPLATE_WEDSTRIJDEN = 'scheidsrechter/wedstrijden.dtl'
TEMPLATE_WEDSTRIJD_DETAILS = 'scheidsrechter/wedstrijd-details.dtl'


class WedstrijdenView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.is_cs = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        if rol_nu == Rollen.ROL_CS:
            self.is_cs = True
            return True
        if rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vorige_week = timezone.now().date() - datetime.timedelta(days=7)

        if self.is_cs:
            wedstrijd_pks = list(WedstrijdDagScheidsrechters
                                 .objects
                                 .order_by('wedstrijd__pk')
                                 .distinct('wedstrijd__pk')
                                 .values_list('wedstrijd__pk', flat=True))
        else:
            wedstrijd_pks = list()

        wedstrijden = (Wedstrijd
                       .objects
                       .exclude(status=WEDSTRIJD_STATUS_ONTWERP)
                       .exclude(is_ter_info=True)
                       .exclude(toon_op_kalender=False)
                       .filter(aantal_scheids__gte=1,
                               datum_begin__gte=vorige_week)
                       .select_related('locatie')
                       .order_by('-datum_begin'))       # nieuwste bovenaan

        for wedstrijd in wedstrijden:
            wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]
            if wedstrijd.organisatie == ORGANISATIE_WA:
                wedstrijd.organisatie_str += ' ' + WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

            wedstrijd.url_details = reverse('Scheidsrechter:wedstrijd-details',
                                            kwargs={'wedstrijd_pk': wedstrijd.pk})

            wedstrijd.nog_opvragen = self.is_cs and (wedstrijd.pk not in wedstrijd_pks)
        # for

        context['wedstrijden'] = wedstrijden
        context['is_cs'] = self.is_cs

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Wedstrijden')
        )

        return context


class WedstrijdDetailsView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJD_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        if self.rol_nu == Rollen.ROL_CS:
            return True
        if self.rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .exclude(status=WEDSTRIJD_STATUS_ONTWERP)
                         .exclude(is_ter_info=True)
                         .exclude(toon_op_kalender=False)
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        wedstrijd.organisatie_str = WEDSTRIJD_ORGANISATIE_TO_STR[wedstrijd.organisatie]

        wedstrijd.begrenzing_str = WEDSTRIJD_BEGRENZING_TO_STR[wedstrijd.begrenzing]

        if wedstrijd.organisatie == ORGANISATIE_WA:
            context['toon_wa_status'] = True
            wedstrijd.wa_status_str = WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]

        toon_kaart = wedstrijd.locatie.plaats != '(diverse)' and wedstrijd.locatie.adres != '(diverse)'
        if toon_kaart:
            zoekterm = wedstrijd.locatie.adres
            if wedstrijd.locatie.adres_uit_crm:
                # voeg de naam van de vereniging toe aan de zoekterm, voor beter resultaat
                zoekterm = wedstrijd.organiserende_vereniging.naam + ' ' + zoekterm
            zoekterm = zoekterm.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
            context['url_map'] = 'https://google.nl/maps?' + urlencode({'q': zoekterm})

        sessie_pks = list(wedstrijd.sessies.values_list('pk', flat=True))
        context['sessies'] = sessies = (WedstrijdSessie
                                        .objects
                                        .filter(pk__in=sessie_pks)
                                        .prefetch_related('wedstrijdklassen')
                                        .order_by('datum',
                                                  'tijd_begin',
                                                  'pk'))

        heeft_sessies = False
        for sessie in sessies:
            heeft_sessies = True
            sessie.klassen = sessie.wedstrijdklassen.order_by('volgorde')

            if wedstrijd.organisatie == ORGANISATIE_IFAA:
                # voeg afkorting toe aan klasse beschrijving
                for klasse in sessie.klassen:
                    klasse.beschrijving += ' [%s]' % klasse.afkorting
                # for
        # for
        context['toon_sessies'] = heeft_sessies

        wedstrijd.behoefte_str = '%s scheidsrechter' % wedstrijd.aantal_scheids
        if wedstrijd.aantal_scheids > 1:
            wedstrijd.behoefte_str += 's'

        if self.rol_nu == Rollen.ROL_CS:
            context['url_wijzigen'] = reverse('Scheidsrechter:wedstrijd-details',
                                              kwargs={'wedstrijd_pk': wedstrijd.pk})

            context['keuze_aantal_scheids'] = [
                (1, '1 scheidsrechter'),
                (2, '2 scheidsrechters'),
                (3, '3 scheidsrechters'),
                (4, '4 scheidsrechters'),
                (5, '5 scheidsrechters'),
                (6, '6 scheidsrechters'),
                (7, '7 scheidsrechters'),
                (8, '8 scheidsrechters'),
                (9, '9 scheidsrechters'),
            ]

            context['hulp_sr'] = hulp_sr = list()
            for lp in range(wedstrijd.aantal_scheids-1):
                beschikbaar_sr = SimpleNamespace()
                hulp_sr.append(beschikbaar_sr)
            # for

            # knop om behoefte op te vragen
            aantal_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
            if WedstrijdDagScheidsrechters.objects.filter(wedstrijd=wedstrijd).count() < aantal_dagen:
                context['url_opvragen'] = reverse('Scheidsrechter:beschikbaarheid-opvragen')

            context['dagen'] = dagen = list()
            for dag in (WedstrijdDagScheidsrechters
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .select_related('gekozen_hoofd_sr',
                                        'gekozen_sr1', 'gekozen_sr2', 'gekozen_sr3', 'gekozen_sr4', 'gekozen_sr5',
                                        'gekozen_sr6', 'gekozen_sr7', 'gekozen_sr8', 'gekozen_sr9')
                        .order_by('dag_offset')):

                datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)

                beschikbaar_hsr = list()
                beschikbaar_sr = list()
                bevat_fouten = False

                geen_hsr = SimpleNamespace(
                                    pk='geen',
                                    scheids=None,
                                    is_selected=dag.gekozen_hoofd_sr is None,
                                    id_li='id_hsr_%s_geen' % dag.dag_offset,
                                    is_onzeker=False,
                                    sel='geen')
                beschikbaar_hsr.append(geen_hsr)

                # voeg de beschikbare hoofdscheidsrechter toe
                hsr_nog_beschikbaar = False
                for beschikbaar in (ScheidsBeschikbaarheid
                                    .objects
                                    .filter(wedstrijd=wedstrijd,
                                            datum=datum,
                                            opgaaf=BESCHIKBAAR_JA)
                                    .exclude(scheids__scheids=SCHEIDS_VERENIGING)  # mag geen hoofdscheidsrechter zijn
                                    .select_related('scheids')
                                    .order_by('scheids__lid_nr')):

                    beschikbaar.id_li = 'id_hsr_%s' % beschikbaar.pk
                    beschikbaar.is_onzeker = (beschikbaar.opgaaf == BESCHIKBAAR_DENK)
                    beschikbaar.is_selected = (dag.gekozen_hoofd_sr == beschikbaar.scheids)
                    hsr_nog_beschikbaar |= (dag.gekozen_hoofd_sr == beschikbaar.scheids)

                    beschikbaar_hsr.append(beschikbaar)
                # for

                if not hsr_nog_beschikbaar and dag.gekozen_hoofd_sr:
                    # gekozen hoofdscheidsrechter is niet meer beschikbaar
                    bevat_fouten = True
                    niet_meer_hsr = SimpleNamespace(
                                        pk=0,       # wordt gebruikt als value
                                        id_li='id_hsr_niet_%s' % dag.gekozen_hoofd_sr.pk,
                                        scheids=dag.gekozen_hoofd_sr,
                                        is_selected=True,
                                        waarschuw_niet_meer_beschikbaar=True)
                    beschikbaar_hsr.insert(1, niet_meer_hsr)

                gekozen_srs = [gekozen_sr.pk
                               for gekozen_sr in (dag.gekozen_sr1, dag.gekozen_sr2, dag.gekozen_sr3,
                                                  dag.gekozen_sr4, dag.gekozen_sr5, dag.gekozen_sr6,
                                                  dag.gekozen_sr7, dag.gekozen_sr8, dag.gekozen_sr9)
                               if gekozen_sr is not None]

                # haal de beschikbare scheidsrechters op
                for beschikbaar in (ScheidsBeschikbaarheid
                                    .objects
                                    .filter(wedstrijd=wedstrijd,
                                            datum=datum)
                                    .exclude(opgaaf=BESCHIKBAAR_NEE)
                                    .select_related('scheids')
                                    .order_by('scheids__lid_nr')):

                    beschikbaar.id_li = 'id_sr_%s' % beschikbaar.pk
                    beschikbaar.sel = 'sr_%s_%s' % (dag.dag_offset, beschikbaar.pk)
                    beschikbaar.is_onzeker = (beschikbaar.opgaaf == BESCHIKBAAR_DENK)
                    if beschikbaar.scheids.pk in gekozen_srs:
                        beschikbaar.is_selected = True
                        gekozen_srs.remove(beschikbaar.scheids.pk)
                    else:
                        beschikbaar.is_selected = False

                    beschikbaar.waarschuw_niet_meer_beschikbaar = beschikbaar.is_selected and beschikbaar.opgaaf != BESCHIKBAAR_JA
                    if beschikbaar.waarschuw_niet_meer_beschikbaar:
                        bevat_fouten = True
                        beschikbaar.is_onzeker = False  # voorkom disable van checkbox

                    beschikbaar_sr.append(beschikbaar)
                # for

                # kijk welke scheidsrechters nog over zijn en dus niet meer kunnen
                for gekozen_sr in (dag.gekozen_sr1, dag.gekozen_sr2, dag.gekozen_sr3,
                                   dag.gekozen_sr4, dag.gekozen_sr5, dag.gekozen_sr6,
                                   dag.gekozen_sr7, dag.gekozen_sr8, dag.gekozen_sr9):

                    if gekozen_sr and gekozen_sr.pk in gekozen_srs:
                        niet_meer_sr = SimpleNamespace(
                                        id_li='id_sr_niet_%s' % gekozen_sr.pk,
                                        sel='sr_%s_niet_%s' % (dag.dag_offset, gekozen_sr.pk),
                                        scheids=gekozen_sr,
                                        is_selected=True,
                                        waarschuw_niet_meer_beschikbaar=True)
                        beschikbaar_sr.insert(0, niet_meer_sr)
                        bevat_fouten = True
                # for

                dag = SimpleNamespace(
                        datum=datum,
                        nr_hsr="hsr_%s" % dag.dag_offset,
                        beschikbaar_hoofd_sr=beschikbaar_hsr,
                        beschikbaar_sr=beschikbaar_sr,
                        bevat_fouten=bevat_fouten)
                dagen.append(dag)
            # for

            context['url_notify'] = context['url_wijzigen']
            for dag in dagen:
                if dag.bevat_fouten:
                    context['url_notify'] = None
            # for

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:wedstrijden'), 'Wedstrijden'),
            (None, 'Details'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        # print('POST: %s' % repr(list(request.POST.items())))

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu != Rollen.ROL_CS:
            raise PermissionDenied('Mag niet wijzigen')

        # aantal scheidsrechters
        aantal_scheids_str = request.POST.get('aantal_scheids', '')
        try:
            aantal_scheids = int(aantal_scheids_str[:3])  # afkappen voor de veiligheid
        except ValueError:
            wedstrijd.aantal_scheids = 1        # minimum is 1, anders verdwijnt de wedstrijd uit de lijst
        else:
            if 0 <= aantal_scheids <= 9:
                wedstrijd.aantal_scheids = aantal_scheids
                # TODO: bij wijziging 1 naar >1 moeten we beschikbaarheid SR3 op gaan vragen

        wedstrijd.save(update_fields=['aantal_scheids'])

        do_notify = False

        # koppel de scheidsrechters voor elke dag
        for dag in WedstrijdDagScheidsrechters.objects.filter(wedstrijd=wedstrijd).order_by('dag_offset'):
            datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)

            # haal de radiobutton keuze op
            nr_hsr = "hsr_%s" % dag.dag_offset
            gekozen = request.POST.get(nr_hsr, '')
            gekozen = str(gekozen)[:6]      # afkappen voor de veiligheid
            if gekozen:
                if gekozen == 'geen':
                    dag.gekozen_hoofd_sr = None
                else:
                    try:
                        pk = int(gekozen)
                        beschikbaar = (ScheidsBeschikbaarheid
                                       .objects
                                       .filter(wedstrijd=wedstrijd,
                                               datum=datum,
                                               opgaaf=BESCHIKBAAR_JA)           # exclude NEE en DENK
                                       .select_related('scheids')
                                       .get(pk=pk))
                    except (ValueError, ScheidsBeschikbaarheid.DoesNotExist):
                        raise Http404('Slechte parameter (1)')

                    dag.gekozen_hoofd_sr = beschikbaar.scheids

            # kijk welke scheidsrechters gekozen zijn
            gekozen_srs = list()
            for beschikbaar in (ScheidsBeschikbaarheid
                                .objects
                                .filter(wedstrijd=wedstrijd,
                                        datum=datum)
                                .filter(opgaaf=BESCHIKBAAR_JA)      # exclude NEE en DENK
                                .select_related('scheids')):

                sel = 'sr_%s_%s' % (dag.dag_offset, beschikbaar.pk)
                gekozen = request.POST.get(sel, '')
                if gekozen:
                    if dag.gekozen_hoofd_sr != beschikbaar.scheids:
                        gekozen_srs.append(beschikbaar.scheids)
            # for

            # zorg dat er minimaal 9 entries in de lijst staan
            gekozen_srs.extend([None]*9)

            dag.gekozen_sr1 = gekozen_srs[0]
            dag.gekozen_sr2 = gekozen_srs[1]
            dag.gekozen_sr3 = gekozen_srs[2]
            dag.gekozen_sr4 = gekozen_srs[3]
            dag.gekozen_sr5 = gekozen_srs[4]
            dag.gekozen_sr6 = gekozen_srs[5]
            dag.gekozen_sr7 = gekozen_srs[6]
            dag.gekozen_sr8 = gekozen_srs[7]
            dag.gekozen_sr9 = gekozen_srs[8]

            dag.save(update_fields=['gekozen_hoofd_sr',
                                    'gekozen_sr1', 'gekozen_sr2', 'gekozen_sr3', 'gekozen_sr4', 'gekozen_sr5',
                                    'gekozen_sr6', 'gekozen_sr7', 'gekozen_sr8', 'gekozen_sr9'])
        # for

        do_notify = str(request.POST.get('notify', ''))[:1] == 'J'
        if do_notify:
            account = get_account(request)
            door_str = "CS %s" % account.volledige_naam()

            snel = str(request.POST.get('snel', ''))[:1]

            scheids_mutatieverzoek_stuur_notificaties(wedstrijd, door_str, snel == '1')

        url = reverse('Scheidsrechter:wedstrijden')
        return HttpResponseRedirect(url)

# end of file
