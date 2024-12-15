# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.views import View
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.utils import timezone
from Account.models import get_account
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import SCHEIDS_BOND, SCHEIDS_INTERNATIONAAL, SCHEIDS_NIET
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, gebruiker_is_scheids
from Locatie.models import Reistijd
from Scheidsrechter.definities import (BESCHIKBAAR_LEEG, BESCHIKBAAR_JA, BESCHIKBAAR_DENK, BESCHIKBAAR_NEE,
                                       BESCHIKBAAR2STR, SCHEIDS2LEVEL)
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsBeschikbaarheid
from Scheidsrechter.mutaties import (scheids_mutatieverzoek_beschikbaarheid_opvragen,
                                     scheids_mutatieverzoek_competitie_beschikbaarheid_opvragen)
from Sporter.models import get_sporter, Sporter
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
from collections import OrderedDict
import datetime

TEMPLATE_BESCHIKBAARHEID_WIJZIGEN = 'scheidsrechter/beschikbaarheid-wijzigen.dtl'
TEMPLATE_BESCHIKBAARHEID_INZIEN_CS = 'scheidsrechter/beschikbaarheid-inzien-cs.dtl'
TEMPLATE_BESCHIKBAARHEID_STATS_CS = 'scheidsrechter/beschikbaarheid-stats-cs.dtl'


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
        return rol_nu == Rol.ROL_CS

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
                              # is_ter_info=False,
                              toon_op_kalender=True))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        account = get_account(request)
        door_str = "CS %s" % account.volledige_naam()

        scheids_mutatieverzoek_beschikbaarheid_opvragen(wedstrijd, door_str, snel == '1')

        url = reverse('Scheidsrechter:overzicht')
        return HttpResponseRedirect(url)


class BeschikbaarheidCompetitieOpvragenView(UserPassesTestMixin, View):

    """ Deze view wordt gebruikt als iemand van de Commissie Scheidsrechters de beschikbaarheid voor
        de bondscompetitie Indoor op wil vragen. De achtergrondtaak handelt dit af.
    """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rol.ROL_CS

    @staticmethod
    def post(request, *args, **kwargs):
        """
            deze functie wordt aangeroepen als op de knop Beschikbaarheid Opvragen gedrukt is.
        """

        snel = str(request.POST.get('snel', ''))[:1]

        account = get_account(request)
        door_str = "CS %s" % account.volledige_naam()

        scheids_mutatieverzoek_competitie_beschikbaarheid_opvragen(door_str, snel == '1')

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
        if self.rol_nu == Rol.ROL_SPORTER and gebruiker_is_scheids(self.request):
            self.account = get_account(self.request)
            self.sporter = get_sporter(self.account)
            self.is_sr4_of_hoger = self.sporter.scheids in (SCHEIDS_INTERNATIONAAL, SCHEIDS_BOND)
            return True
        return False

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vandaag = timezone.now().date()
        vorige_week = vandaag - datetime.timedelta(days=7)

        # wedstrijden in de toekomst
        wedstrijd_pks = list(Wedstrijd
                             .objects
                             .filter(aantal_scheids__gte=1,
                                     status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                     datum_einde__gte=vorige_week)
                             #.exclude(is_ter_info=True)
                             .values_list('pk', flat=True))

        # kijk voor welke dagen we beschikbaarheid nodig hebben
        dagen = (WedstrijdDagScheidsrechters
                 .objects
                 .select_related('wedstrijd',
                                 'wedstrijd__locatie')
                 .filter(wedstrijd__pk__in=wedstrijd_pks)
                 .order_by('wedstrijd__datum_begin',       # chronologische volgorde
                           'dag_offset',
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

            dag.mag_wijzigen = datum >= vandaag

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
        opmerking = dict()  # [datum] = opmerking
        for keuze in ScheidsBeschikbaarheid.objects.filter(datum__in=datums, scheids=self.sporter):
            datum = keuze.datum
            idx = (keuze.datum, keuze.wedstrijd.pk)
            if keuze.opgaaf == BESCHIKBAAR_JA:
                keuzes[idx] = 1
            elif keuze.opgaaf == BESCHIKBAAR_DENK:
                keuzes[idx] = 2
            elif keuze.opgaaf == BESCHIKBAAR_NEE:
                keuzes[idx] = 3
            else:
                keuzes[idx] = 0
            opmerking[idx] = keuze.opmerking
        # for

        context['dagen'] = dagen
        for dag in dagen:
            dag.datum = dag.wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
            dag.id = "dag-%s" % dag.pk
            dag.name = 'wedstrijd_%s_dag_%s' % (dag.wedstrijd.pk, dag.dag_offset)
            dag.keuze = 0
            dag.opmerking = ''
            idx = (dag.datum, dag.wedstrijd.pk)
            try:
                dag.keuze = keuzes[idx]
                dag.opmerking = opmerking[idx]
            except KeyError:
                pass
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

        # print('POST: %s' % repr(list(request.POST.items())))

        vorige_week = (timezone.now() - datetime.timedelta(days=7)).date()

        # wedstrijden in de toekomst
        wedstrijd_pks = list(Wedstrijd
                             .objects
                             .filter(aantal_scheids__gte=1,
                                     status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                     datum_einde__gte=vorige_week)
                             #.exclude(is_ter_info=True)
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
            keuze = request.POST.get(name, '')[:6]                       # afkappen voor de veiligheid
            opmerking = request.POST.get(name + '-opmerking', '')[:100]  # afkappen voor de veiligheid

            if keuze in ('1', '2', '3'):
                try:
                    tup = (dag.datum, dag.wedstrijd.pk)
                    beschikbaar = cache[tup]
                except KeyError:
                    beschikbaar = ScheidsBeschikbaarheid(
                                        scheids=self.sporter,
                                        wedstrijd=dag.wedstrijd,
                                        datum=dag.datum)

                do_save = False

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
                    do_save = True

                if opmerking != beschikbaar.opmerking:
                    beschikbaar.log += '[%s] Notitie: %s\n' % (when_str, opmerking)
                    beschikbaar.opmerking = opmerking
                    do_save = True

                if do_save:
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
        return rol_get_huidige(self.request) == Rol.ROL_CS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        vorige_week = (timezone.now() - datetime.timedelta(days=7)).date()

        dagen = (WedstrijdDagScheidsrechters
                 .objects
                 .select_related('wedstrijd',
                                 'wedstrijd__locatie')
                 .filter(wedstrijd__datum_einde__gte=vorige_week)
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
                       SCHEIDS2LEVEL[keuze.scheids.scheids],
                       keuze.scheids.volledige_naam(),
                       BESCHIKBAAR2STR[keuze.opgaaf],
                       keuze.opmerking,
                       is_hsr,
                       is_sr,
                       is_probleem)

                dag.beschikbaar.append(tup)
            # for

            dag.beschikbaar.sort()   # sorteer op opgaaf, dan op naam
            dag.beschikbaar = [tup[2:] for tup in dag.beschikbaar]
            dag.aantal = len(dag.beschikbaar)
        # for

        context['url_stats'] = reverse('Scheidsrechter:beschikbaarheid-stats')

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (None, 'Beschikbaarheid')
        )

        return context


class BeschikbaarheidStatsCSView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de Commissie Scheidsrechters
        om statistiek over de opgegeven beschikbaarheid te krijgen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESCHIKBAARHEID_STATS_CS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return rol_get_huidige(self.request) == Rol.ROL_CS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        opgaaf2str = {
            BESCHIKBAAR_JA: 'ja',
            BESCHIKBAAR_DENK: 'denk',
            BESCHIKBAAR_NEE: 'nee',
            BESCHIKBAAR_LEEG: 'leeg',
        }

        context['counts'] = counts = OrderedDict()

        for obj in Sporter.objects.exclude(scheids=SCHEIDS_NIET).order_by('lid_nr'):
            sr_counts = {'opmerking': 0,
                         'naam': obj.volledige_naam(),
                         'level_str': SCHEIDS2LEVEL[obj.scheids]}
            for opgaaf in opgaaf2str.values():
                sr_counts[opgaaf] = 0
            # for
            counts[obj.lid_nr] = sr_counts
        # for

        for obj in (ScheidsBeschikbaarheid
                    .objects
                    .select_related('scheids')):

            lid_nr = obj.scheids.lid_nr
            if lid_nr in counts:
                counts[lid_nr][opgaaf2str[obj.opgaaf]] += 1
                if obj.opmerking:
                    counts[lid_nr]['opmerking'] += 1
        # for

        for count in counts.values():
            count['totaal'] = totaal = count['ja'] + count['denk'] + count['nee']
            if totaal == 0:
                totaal = 0.00001
            count['ja_perc'] = '%.0f%%' % ((count['ja'] * 100) / totaal)
            count['denk_perc'] = '%.0f%%' % ((count['denk'] * 100) / totaal)
            count['nee_perc'] = '%.0f%%' % ((count['nee'] * 100) / totaal)

        context['kruimels'] = (
            (reverse('Scheidsrechter:overzicht'), 'Scheidsrechters'),
            (reverse('Scheidsrechter:beschikbaarheid-inzien'), 'Beschikbaarheid'),
            (None, 'Statistiek')
        )

        return context


# end of file
