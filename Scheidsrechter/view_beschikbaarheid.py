# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import render
from Account.models import get_account
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Functie.scheids import gebruiker_is_scheids
from Locatie.models import Reistijd
from Scheidsrechter.definities import BESCHIKBAAR_LEEG, BESCHIKBAAR_JA, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE, BESCHIKBAAR2STR
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid
from Scheidsrechter.mutaties import scheids_mutatieverzoek_beschikbaarheid_opvragen
from Sporter.models import Sporter, get_sporter
from TijdelijkeCodes.definities import RECEIVER_SCHEIDS_BESCHIKBAAR
from TijdelijkeCodes.operations import set_tijdelijke_codes_receiver
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
import datetime

TEMPLATE_BESCHIKBAARHEID_WIJZIGEN = 'scheidsrechter/beschikbaarheid-wijzigen.dtl'
TEMPLATE_BESCHIKBAARHEID_INZIEN = 'scheidsrechter/beschikbaarheid-inzien.dtl'


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
                 .order_by('wedstrijd__datum_begin',
                           'wedstrijd__pk'))

        lat_lon2reistijd_min = dict()
        for reistijd in Reistijd.objects.filter(vanaf_lat=self.sporter.adres_lat, vanaf_lon=self.sporter.adres_lon):
            lat_lon2reistijd_min[(reistijd.naar_lat, reistijd.naar_lon)] = reistijd.reistijd_min

        datums = list()
        for dag in dagen:
            datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            if datum not in datums:
                datums.append(datum)

            dag.reistijd = "?"
            if self.sporter.adres_lat:
                locatie = dag.wedstrijd.locatie
                if locatie.adres_lat:
                    try:
                        reistijd = lat_lon2reistijd_min[(locatie.adres_lat, locatie.adres_lon)]
                        if reistijd > 0:
                            dag.reistijd = reistijd
                    except KeyError:
                        pass
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

                opgaaf = BESCHIKBAAR_LEEG
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


class BeschikbaarheidInzienView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de Commissie Scheidsrechters om de opgaaf van de SR's te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_BESCHIKBAARHEID_INZIEN
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
                 .order_by('wedstrijd__datum_begin',
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
                keuzes = wedstrijd_dag2beschikbaar[tup]
            except KeyError:
                keuzes = list()

            for keuze in keuzes:
                tup = (opgaaf2order[keuze.opgaaf], keuze.scheids.volledige_naam(), BESCHIKBAAR2STR[keuze.opgaaf])
                dag.beschikbaar.append(tup)
            # for

            dag.beschikbaar.sort()   # sorteer op opgaaf, dan op naam
        # for

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Beschikbaarheid')
        )

        return context


class BeschikbaarheidOpslaanView(View):
    """ Behandel de ingediende wijziging """

    @staticmethod
    def post(request, *args, **kwargs):
        """
            deze functie wordt aangeroepen als op de knop GA DOOR gedrukt
            is na het volgen van een tijdelijke url.
            Zoek de bijbehorende data op en roept de juiste dispatcher aan.
        """

        wedstrijd_pk = request.POST.get('wedstrijd', '')[:6]    # afkappen voor de veiligheid
        scheids_pk = request.POST.get('scheids', '')[:6]        # afkappen voor de veiligheid
        keuze = request.POST.get('keuze', '')[:1]               # afkappen voor de veiligheid

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

        if request.user.is_authenticated:
            # namens zichzelf
            account = get_account(request)
            sporter = get_sporter(account)
            if scheids_pk != sporter.pk:
                raise Http404('Verkeerde gebruiker')

            url = reverse('Scheidsrechter:overzicht')

        else:
            # niet ingelogd, dus dit is via de tijdelijke code
            try:
                sporter_pk = int(scheids_pk)
                sporter = (Sporter
                           .objects
                           .exclude(scheids=SCHEIDS_NIET)
                           .get(pk=sporter_pk))
            except (ValueError, Sporter.DoesNotExist):
                raise Http404('Gebruiker niet gevonden')

            url = reverse('Plein:plein')

        # kijk voor welke dagen we beschikbaarheid nodig hebben
        dagen = WedstrijdDagScheids.objects.filter(wedstrijd=wedstrijd)


        return HttpResponseRedirect(url)


def receive_scheids_beschikbaarheid(request, wedstrijd, sporter):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        door een scheidsrechter om zijn beschikbaarheid voor een wedstrijd door te geven.

        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.

        We geven een pagina terug waarop de keuzes gemaakt kunnen worden en ingediend worden.
    """

    context = dict()
    context['url'] = reverse('Scheidsrechter:beschikbaarheid-doorgeven')
    context['wedstrijd'] = wedstrijd
    context['scheids'] = sporter

    return render(request, TEMPLATE_BESCHIKBAARHEID, context)


set_tijdelijke_codes_receiver(RECEIVER_SCHEIDS_BESCHIKBAAR, receive_scheids_beschikbaarheid)


# end of file
