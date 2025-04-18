# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Sporter.models import Sporter
from Wedstrijden.definities import WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING, WEDSTRIJD_KORTING_COMBI
from Wedstrijden.models import Wedstrijd, WedstrijdKorting
import datetime

TEMPLATE_WEDSTRIJDEN_KORTINGEN_OVERZICHT = 'wedstrijden/kortingen-overzicht.dtl'
TEMPLATE_WEDSTRIJDEN_NIEUWE_KORTING = 'wedstrijden/korting-nieuw-kies.dtl'
TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_SPORTER = 'wedstrijden/wijzig-korting-sporter.dtl'
TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_VERENIGING = 'wedstrijden/wijzig-korting-vereniging.dtl'
TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_COMBI = 'wedstrijden/wijzig-korting-combi.dtl'


class KortingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL de kortingen van de vereniging beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_KORTINGEN_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
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

        ver = self.functie_nu.vereniging

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        kortingen = (WedstrijdKorting
                     .objects
                     .filter(uitgegeven_door=ver)
                     .select_related('voor_sporter')
                     .order_by('geldig_tot_en_met',
                               'pk'))       # in geval van gelijk datum

        for korting in kortingen:
            korting.voor_wie_str = '-'
            korting.voor_wedstrijden_str = '\n'.join(korting
                                                     .voor_wedstrijden
                                                     .order_by('datum_begin', 'pk')
                                                     .values_list('titel', flat=True))

            if korting.soort == WEDSTRIJD_KORTING_SPORTER:
                korting.icon_name = 'account_circle'
                if korting.voor_sporter:
                    korting.voor_wie_str = korting.voor_sporter.lid_nr_en_volledige_naam()

            elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
                korting.icon_name = 'home'
                korting.voor_wie_str = 'Leden van vereniging %s' % ver.ver_nr

            elif korting.soort == WEDSTRIJD_KORTING_COMBI:       # pragma: no branch
                korting.icon_name = 'join_full'

            else:       # pragma: no cover
                korting.voor_wie_str = "?"

            korting.url_wijzig = reverse('Wedstrijden:vereniging-korting-wijzig', kwargs={'korting_pk': korting.pk})
        # for

        context['kortingen'] = kortingen

        context['url_nieuwe_korting'] = reverse('Wedstrijden:vereniging-korting-nieuw-kies')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (None, 'Kortingen'),
        )

        return context


class KiesNieuweKortingView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een nieuwe korting van de vereniging aanmaken """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_NIEUWE_KORTING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        context['url_nieuwe_korting'] = reverse('Wedstrijden:vereniging-korting-nieuw-kies')

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:vereniging-kortingen'), 'Kortingen'),
            (None, 'Nieuwe aanmaken')
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de HWL een nieuwe korting aan wil maken """

        ver = self.functie_nu.vereniging
        toekomst = timezone.now().date() + datetime.timedelta(days=30)

        korting = WedstrijdKorting(
                        geldig_tot_en_met=toekomst,
                        uitgegeven_door=ver)

        keuze = request.POST.get('keuze', '')

        if keuze == 'sporter':
            korting.soort = WEDSTRIJD_KORTING_SPORTER
        elif keuze == 'vereniging':
            korting.soort = WEDSTRIJD_KORTING_VERENIGING
        elif keuze == 'combi':
            korting.soort = WEDSTRIJD_KORTING_COMBI
        else:
            raise Http404('Niet ondersteund')

        korting.save()

        url = reverse('Wedstrijden:vereniging-korting-wijzig', kwargs={'korting_pk': korting.pk})

        return HttpResponseRedirect(url)


class WijzigKortingView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een korting van de vereniging beheren """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()
        ver = self.functie_nu.vereniging
        context['ver'] = ver

        try:
            korting_pk = kwargs['korting_pk'][:6]       # afkappen voor de veiligheid
            korting_pk = int(korting_pk)
            korting = (WedstrijdKorting
                       .objects
                       .select_related('voor_sporter')
                       .get(pk=korting_pk,
                            uitgegeven_door=ver))
        except (ValueError, TypeError, WedstrijdKorting.DoesNotExist):
            raise Http404('Niet gevonden')

        context['korting'] = korting
        korting.sporter_lid_nr = ''

        if korting.soort == WEDSTRIJD_KORTING_SPORTER:
            template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_SPORTER
            if korting.voor_sporter:
                context['voor_sporter_str'] = korting.voor_sporter.lid_nr_en_volledige_naam()
                korting.sporter_lid_nr = korting.voor_sporter.lid_nr

        elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
            template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_VERENIGING
            context['check_ver'] = True

        elif korting.soort == WEDSTRIJD_KORTING_COMBI:                           # pragma: no branch
            template_name = TEMPLATE_WEDSTRIJDEN_WIJZIG_KORTING_COMBI

        else:                                                                   # pragma: no cover
            raise Http404('Niet ondersteund')

        gekozen_pks = list(korting.voor_wedstrijden.all().values_list('pk', flat=True))

        context['wedstrijden'] = wedstrijden = list()
        # TODO: wedstrijden uit het verleden uit deze lijst filteren
        for wedstrijd in (Wedstrijd
                          .objects
                          .filter(organiserende_vereniging=ver)
                          .exclude(titel='')
                          .order_by('datum_begin',      # welke komt nu eerst?
                                    'pk')):             # voor wedstrijden op dezelfde dag toch standard volgorde

            wedstrijd.sel = 'wedstrijd_%s' % wedstrijd.pk
            if wedstrijd.pk in gekozen_pks:
                wedstrijd.is_gekozen = True

            wedstrijden.append(wedstrijd)
        # for

        # nodig voor de datum picker
        # zorg dat de huidige datum weer gekozen kan worden
        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, korting.geldig_tot_en_met.year)
        context['min_date'] = min(now.date(), korting.geldig_tot_en_met)
        context['max_date'] = datetime.date(now.year + 2, 12, 31)

        context['url_opslaan'] = reverse('Wedstrijden:vereniging-korting-wijzig', kwargs={'korting_pk': korting.pk})

        # verwijderen kan alleen als deze nog niet gebruikt is
        if korting.wedstrijdinschrijving_set.count() == 0:
            context['url_verwijder'] = context['url_opslaan']

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:vereniging-kortingen'), 'Kortingen'),
            (None, 'Wijzig'),
        )

        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'opslaan' gebruikt wordt door de HWL """

        onze_ver = self.functie_nu.vereniging

        try:
            korting_pk = kwargs['korting_pk'][:6]       # afkappen voor de veiligheid
            korting_pk = int(korting_pk)
            korting = WedstrijdKorting.objects.get(pk=korting_pk,
                                                   uitgegeven_door=onze_ver)
        except (ValueError, TypeError, WedstrijdKorting.DoesNotExist):
            raise Http404('Niet gevonden')

        if request.POST.get('verwijder', ''):
            # verwijderen deze korting
            if korting.wedstrijdinschrijving_set.count() > 0:
                raise Http404('Korting is in gebruik')
            korting.delete()
        else:
            try:
                percentage = request.POST.get('percentage', '100')[:3]      # afkappen voor de veiligheid
                percentage = int(percentage)
            except (ValueError, KeyError, TypeError):
                raise Http404('Verkeerde parameter (percentage)')

            # kortingspercentage
            if not (0 <= percentage <= 100):
                raise Http404('Verkeerd percentage')
            korting.percentage = percentage

            # geldigheidsdatum
            datum_ymd = request.POST.get('geldig_tm', '')[:10]  # afkappen voor de veiligheid
            if datum_ymd:
                try:
                    datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
                except ValueError:
                    raise Http404('Geen valide datum')

                datum = datetime.date(datum.year, datum.month, datum.day)
                now = timezone.now()
                min_date = datetime.date(now.year, now.month, now.day)
                max_date = datetime.date(now.year + 2, 12, 31)
                if min_date <= datum <= max_date:
                    korting.geldig_tot_en_met = datum
                else:
                    raise Http404('Geen valide datum')

            # selectie van de sporter
            if korting.soort == WEDSTRIJD_KORTING_SPORTER:
                voor_lid_nr = request.POST.get('voor_lid_nr', '')[:6]           # afkappen voor de veiligheid
                if voor_lid_nr:
                    if voor_lid_nr == '000000':
                        korting.voor_sporter = None
                    else:
                        try:
                            voor_lid_nr = int(voor_lid_nr)
                            sporter = Sporter.objects.get(lid_nr=voor_lid_nr)
                        except (ValueError, TypeError, Sporter.DoesNotExist):
                            raise Http404('Sporter niet gevonden')

                        korting.voor_sporter = sporter

            korting.save()

            # selectie van wedstrijden
            wedstrijd_pks = list()
            # TODO: begrens wedstrijden op datum (net als in GET)
            for wedstrijd in (Wedstrijd
                              .objects
                              .filter(organiserende_vereniging=onze_ver)):

                pk = wedstrijd.pk
                sel = 'wedstrijd_%s' % pk
                if request.POST.get(sel, ''):
                    wedstrijd_pks.append(pk)
            # for
            korting.voor_wedstrijden.set(wedstrijd_pks)

        url = reverse('Wedstrijden:vereniging-kortingen')
        return HttpResponseRedirect(url)


# end of file
