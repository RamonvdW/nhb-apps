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
from BasisTypen.definities import ORGANISATIE_IFAA
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Plein.menu import menu_dynamics
from Scheidsrechter.definities import SCHEIDS_VERENIGING, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE
from Scheidsrechter.models import WedstrijdDagScheids, ScheidsBeschikbaarheid
from Wedstrijden.definities import (WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_ORGANISATIE_TO_STR,
                                    ORGANISATIE_WA, WEDSTRIJD_WA_STATUS_TO_STR,
                                    WEDSTRIJD_BEGRENZING_TO_STR)
from Wedstrijden.models import Wedstrijd, WedstrijdSessie
from types import SimpleNamespace
import datetime

TEMPLATE_OVERZICHT = 'scheidsrechter/overzicht.dtl'
TEMPLATE_WEDSTRIJDEN = 'scheidsrechter/wedstrijden.dtl'
TEMPLATE_WEDSTRIJD_DETAILS = 'scheidsrechter/wedstrijd-details.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
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

        if self.rol_nu == Rollen.ROL_SPORTER:
            context['url_korps'] = reverse('Scheidsrechter:korps')
            context['tekst_korps'] = "Bekijk de lijst van de scheidsrechters."

            context['url_beschikbaarheid'] = reverse('Scheidsrechter:beschikbaarheid-wijzigen')
            context['tekst_beschikbaarheid'] = "Pas je beschikbaarheid aan voor wedstrijden."

            context['rol'] = 'sporter / scheidsrechter'
        else:
            context['url_korps'] = reverse('Scheidsrechter:korps-met-contactgegevens')
            context['tekst_korps'] = "Bekijk de lijst van de scheidsrechters met contextgegevens."

            context['url_beschikbaarheid'] = reverse('Scheidsrechter:beschikbaarheid-inzien')
            context['tekst_beschikbaarheid'] = "Bekijk de opgegeven beschikbaarheid."

            context['rol'] = 'Commissie Scheidsrechters'

        context['kruimels'] = (
            (None, 'Scheidsrechters'),
        )

        menu_dynamics(self.request, context)
        return context


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
            wedstrijd_pks = list(WedstrijdDagScheids
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

            wedstrijd.nog_opvragen = (wedstrijd.pk not in wedstrijd_pks)
        # for

        context['wedstrijden'] = wedstrijden

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Wedstrijden')
        )

        menu_dynamics(self.request, context)
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
            sessie.aantal_beschikbaar = sessie.max_sporters - sessie.aantal_inschrijvingen
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
            ]

            context['hulp_sr'] = hulp_sr = list()
            for lp in range(wedstrijd.aantal_scheids-1):
                sr = SimpleNamespace()
                hulp_sr.append(sr)
            # for

            # knop om behoefte op te vragen
            aantal_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
            benodigd = wedstrijd.aantal_scheids * aantal_dagen
            if WedstrijdDagScheids.objects.filter(wedstrijd=wedstrijd).count() < benodigd:
                context['url_opvragen'] = reverse('Scheidsrechter:beschikbaarheid-opvragen')

            context['dagen'] = dagen = list()
            for dag_offset in range(aantal_dagen):
                datum = wedstrijd.datum_begin + datetime.timedelta(days=dag_offset)

                hsr = list()
                sr = list()

                for beschikbaar in (ScheidsBeschikbaarheid
                                    .objects
                                    .filter(wedstrijd=wedstrijd,
                                            datum=datum)
                                    .exclude(opgaaf=BESCHIKBAAR_NEE)
                                    .select_related('scheids')
                                    .order_by('scheids__lid_nr')):

                    # TODO: zet is_selected indien al gekozen
                    beschikbaar.is_selected = False
                    beschikbaar.id_li1 = 'id_%s_1' % beschikbaar.pk
                    beschikbaar.id_li2 = 'id_%s_2' % beschikbaar.pk
                    beschikbaar.is_onzeker = (beschikbaar.opgaaf == BESCHIKBAAR_DENK)

                    sr.append(beschikbaar)
                    if beschikbaar.scheids.scheids != SCHEIDS_VERENIGING:
                        hsr.append(beschikbaar)
                # for

                if len(hsr) > 0 or len(sr) > 0:
                    dag = SimpleNamespace(
                            datum=datum,
                            nr_hsr="hsr_%s" % dag_offset,
                            nr_sr="sr_%s" % dag_offset,
                            beschikbaar_hoofd_sr=hsr,
                            beschikbaar_sr=sr)
                    dagen.append(dag)
            # for

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:wedstrijden'), 'Wedstrijden'),
            (None, 'Details'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

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

        wedstrijd.save(update_fields=['aantal_scheids'])

        url = reverse('Scheidsrechter:wedstrijden')
        return HttpResponseRedirect(url)

# end of file
