# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from Account.models import get_account
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Locatie.models import Reistijd
from Scheidsrechter.definities import (BESCHIKBAAR_LEEG, BESCHIKBAAR_JA, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE,
                                       BESCHIKBAAR2STR, SCHEIDS2LEVEL)
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid
from Scheidsrechter.mutaties import scheids_mutatieverzoek_beschikbaarheid_opvragen
from Sporter.models import get_sporter
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime

TEMPLATE_BESCHIKBAARHEID_WIJZIGEN = 'scheidsrechter/beschikbaarheid-wijzigen.dtl'
TEMPLATE_BESCHIKBAARHEID_INZIEN_CS = 'scheidsrechter/beschikbaarheid-inzien-cs.dtl'


class BeschikbaarheidOpvragenView(UserPassesTestMixin, View):
    """ Deze view wordt gebruikt als iemand van de Commissie Scheidsrechters de behoefte voor een wedstrijd
        op wil vragen. Dit kan ook gebruiker als het aantal scheidsrechters verhoogd is of het aantal dagen
        aangepast is.
    """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_CS

    @staticmethod
    def post(request, *args, **kwargs):
        """
            deze functie wordt aangeroepen als op de knop Beschikbaarheid Opvragen gedrukt is.
        """

        snel = str(request.POST.get('snel', ''))[:1]
        wedstrijd_pk = request.POST.get('wedstrijd', '')[:6]    # afkappen voor de veiligheid

        try:
            wedstrijd_pk = int(wedstrijd_pk)
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk,
                              status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                              toon_op_kalender=True,
                              is_ter_info=False))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        account = get_account(request)
        door_str = "CS %s" % account.volledige_naam()

        scheids_mutatieverzoek_beschikbaarheid_opvragen(wedstrijd, door_str, snel == '1')

        url = reverse('Scheidsrechter:overzicht')
        return HttpResponseRedirect(url)


class WijzigBeschikbaarheidView(UserPassesTestMixin, TemplateView):

    """ Django class-based view voor de scheidsrechters """

    # class variables shared by all instances
    template_name = TEMPLATE_BESCHIKBAARHEID_WIJZIGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.account = None
        self.sporter = None
        self.is_sr4_of_hoger = False

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        if self.rol_nu == Rollen.ROL_SPORTER and gebruiker_is_scheids(self.request):
            self.account = get_account(self.request)
            self.sporter = get_sporter(self.account)
            self.is_sr4_of_hoger = self.sporter.scheids in (SCHEIDS_INTERNATIONAAL, SCHEIDS_BOND)
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vorige_week = (timezone.now() - datetime.timedelta(days=7)).date()

        # wedstrijden in de toekomst
        wedstrijd_pks = list(Wedstrijd
                             .objects
                             .filter(aantal_scheids__gte=1,
                                     status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                     datum_begin__gte=vorige_week)
                             .exclude(is_ter_info=True)
                             .exclude(toon_op_kalender=False)
                             .values_list('pk', flat=True))

        # kijk voor welke dagen we beschikbaarheid nodig hebben
        dagen = (WedstrijdDagScheidsrechters
                 .objects
                 .select_related('wedstrijd',
                                 'wedstrijd__locatie')
                 .filter(wedstrijd__pk__in=wedstrijd_pks)
                 .order_by('wedstrijd__datum_begin',       # chronologische volgorde
                           'wedstrijd__pk'))

        lat_lon2reistijd_min = dict()
        for reistijd in Reistijd.objects.filter(vanaf_lat=self.sporter.adres_lat, vanaf_lon=self.sporter.adres_lon):
            lat_lon2reistijd_min[(reistijd.naar_lat, reistijd.naar_lon)] = reistijd.reistijd_min
        # for

        datums = list()
        for dag in dagen:
            datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            if datum not in datums:
                datums.append(datum)

            if self.sporter.adres_lat:
                locatie = dag.wedstrijd.locatie
                if locatie.adres_lat:
                    try:
                        reistijd = lat_lon2reistijd_min[(locatie.adres_lat, locatie.adres_lon)]
                        if reistijd > 0:
                            dag.reistijd = reistijd
                    except KeyError:
                        pass

            # dag.url_details = reverse('Scheidsrechter:wedstrijd-details', kwargs={'wedstrijd_pk': dag.wedstrijd.pk})
        # for

        keuzes = dict()     # [datum] = keuze
        for keuze in ScheidsBeschikbaarheid.objects.filter(datum__in=datums, scheids=self.sporter):
            datum = keuze.datum
            if keuze.opgaaf == BESCHIKBAAR_JA:
                keuzes[datum] = 1
            elif keuze.opgaaf == BESCHIKBAAR_DENK:
                keuzes[datum] = 2
            elif keuze.opgaaf == BESCHIKBAAR_NEE:
                keuzes[datum] = 3
            else:
                keuzes[datum] = 0
        # for

        context['dagen'] = dagen
        for dag in dagen:
            dag.datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            dag.id = "dag-%s" % dag.pk
            dag.name = 'wedstrijd_%s_dag_%s' % (dag.wedstrijd.pk, dag.dag_offset)
            try:
                dag.keuze = keuzes[dag.datum]
            except KeyError:
                dag.keuze = 0
        # for

        context['url_opslaan'] = reverse('Scheidsrechter:beschikbaarheid-wijzigen')

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Beschikbaarheid')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de OPSLAAN knop gebruikt wordt
            we slaan de gemaakte keuzes op
        """

        vorige_week = (timezone.now() - datetime.timedelta(days=7)).date()

        # wedstrijden in de toekomst
        wedstrijd_pks = list(Wedstrijd
                             .objects
                             .filter(aantal_scheids__gte=1,
                                     status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                     datum_begin__gte=vorige_week)
                             .exclude(is_ter_info=True)
                             .exclude(toon_op_kalender=False)
                             .values_list('pk', flat=True))

        # kijk voor welke dagen we beschikbaarheid nodig hebben
        dagen = (WedstrijdDagScheidsrechters
                 .objects
                 .select_related('wedstrijd')
                 .filter(wedstrijd__pk__in=wedstrijd_pks))

        # beschikbaarheid is voor specifieke datums
        # dus als de wedstrijd verplaatst worden naar een andere datum, dan geldt de beschikbaarheid niet meer
        datums = list()
        for dag in dagen:
            dag.datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            if dag.datum not in datums:
                datums.append(dag.datum)
        # for

        cache = dict()     # [(datum, wedstrijd_pk)] = keuze
        for keuze in (ScheidsBeschikbaarheid
                      .objects
                      .select_related('wedstrijd')
                      .filter(datum__in=datums,
                              scheids=self.sporter,
                              wedstrijd__pk__in=wedstrijd_pks)):
            tup = (keuze.datum, keuze.wedstrijd.pk)
            cache[tup] = keuze
        # for

        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M:%S')

        for dag in dagen:
            name = 'wedstrijd_%s_dag_%s' % (dag.wedstrijd.pk, dag.dag_offset)
            keuze = request.POST.get(name, '')[:6]      # afkappen voor de veiligheid

            if keuze in ('1', '2', '3'):
                try:
                    tup = (dag.datum, dag.wedstrijd.pk)
                    beschikbaar = cache[tup]
                except KeyError:
                    beschikbaar = ScheidsBeschikbaarheid(
                                        scheids=self.sporter,
                                        wedstrijd=dag.wedstrijd,
                                        datum=dag.datum)

                if keuze == '1':
                    opgaaf = BESCHIKBAAR_JA
                elif keuze == '2':
                    opgaaf = BESCHIKBAAR_DENK
                else:   # keuze == '3':
                    opgaaf = BESCHIKBAAR_NEE

                if opgaaf != beschikbaar.opgaaf:
                    beschikbaar.log += '[%s] Opgaaf %s --> %s\n' % (when_str,
                                                                    BESCHIKBAAR2STR[beschikbaar.opgaaf],
                                                                    BESCHIKBAAR2STR[opgaaf])
                    beschikbaar.opgaaf = opgaaf
                    beschikbaar.save()
        # for

        url = reverse('Scheidsrechter:overzicht')
        return HttpResponseRedirect(url)


class BeschikbaarheidInzienCSView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de Commissie Scheidsrechters om de opgaaf van de SR's te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_BESCHIKBAARHEID_INZIEN_CS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rollen.ROL_CS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vorige_week = (timezone.now() - datetime.timedelta(days=7)).date()

        dagen = (WedstrijdDagScheidsrechters
                 .objects
                 .select_related('wedstrijd',
                                 'wedstrijd__locatie')
                 .filter(wedstrijd__datum_begin__gte=vorige_week)
                 .order_by('wedstrijd__datum_begin',       # chronologische volgorde
                           'dag_offset',
                           'wedstrijd__pk'))

        opgaaf2order = {
            BESCHIKBAAR_JA: 1,
            BESCHIKBAAR_DENK: 2,
            BESCHIKBAAR_NEE: 3,
            BESCHIKBAAR_LEEG: 99,
        }

        wedstrijd_pks = list()
        for dag in dagen:
            dag.datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            dag.beschikbaar = list()
            if dag.wedstrijd.pk not in wedstrijd_pks:
                wedstrijd_pks.append(dag.wedstrijd.pk)
        # for

        # alle beschikbaarheid in 1x ophalen
        wedstrijd_dag2beschikbaar = dict()  # [wedstrijd.pk, datum] = [ScheidsBeschikbaar, ..]
        for keuze in (ScheidsBeschikbaarheid
                      .objects
                      .filter(wedstrijd__pk__in=wedstrijd_pks)
                      .select_related('wedstrijd',
                                      'scheids')):

            tup = (keuze.wedstrijd.pk, keuze.datum)
            try:
                wedstrijd_dag2beschikbaar[tup].append(keuze)
            except KeyError:
                wedstrijd_dag2beschikbaar[tup] = [keuze]
        # for

        # beschikbaarheid per dag bepalen
        context['dagen'] = dagen
        for dag in dagen:
            try:
                tup = (dag.wedstrijd.pk, dag.datum)
                beschikbaar = wedstrijd_dag2beschikbaar[tup]
            except KeyError:
                beschikbaar = list()

            srs = [sr
                   for sr in (dag.gekozen_sr1, dag.gekozen_sr2, dag.gekozen_sr3, dag.gekozen_sr4, dag.gekozen_sr5,
                              dag.gekozen_sr6, dag.gekozen_sr7, dag.gekozen_sr8, dag.gekozen_sr9)
                   if sr is not None]

            for keuze in beschikbaar:
                is_hsr = keuze.scheids == dag.gekozen_hoofd_sr
                is_sr = keuze.scheids in srs

                is_probleem = (is_hsr or is_sr) and keuze.opgaaf != BESCHIKBAAR_JA

                tup = (not is_hsr,
                       not is_sr,
                       opgaaf2order[keuze.opgaaf],
                       "%s: %s" % (SCHEIDS2LEVEL[keuze.scheids.scheids], keuze.scheids.volledige_naam()),
                       BESCHIKBAAR2STR[keuze.opgaaf],
                       is_hsr,
                       is_sr,
                       is_probleem)

                dag.beschikbaar.append(tup)
            # for

            dag.beschikbaar.sort()   # sorteer op opgaaf, dan op naam
            dag.beschikbaar = [tup[2:] for tup in dag.beschikbaar]
        # for

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Beschikbaarheid')
        )

        return context


# end of file
