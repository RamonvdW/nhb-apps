# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import ORGANISATIES2SHORT_STR
from Betaal.models import BetaalInstellingenVereniging
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Taken.operations import maak_taak
from Wedstrijden.definities import (ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS, WEDSTRIJD_STATUS_TO_STR,
                                    WEDSTRIJD_STATUS_CHOICES, WEDSTRIJD_STATUS2URL, WEDSTRIJD_URL2STATUS,
                                    WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, WEDSTRIJD_STATUS_ONTWERP,
                                    WEDSTRIJD_STATUS_GEANNULEERD, WEDSTRIJD_STATUS_GEACCEPTEERD)
from Wedstrijden.models import Wedstrijd
from types import SimpleNamespace
import datetime

TEMPLATE_WEDSTRIJDEN_OVERZICHT_MANAGER = 'wedstrijden/overzicht-manager.dtl'


class KalenderManagerView(UserPassesTestMixin, View):
    """ Via deze view kan de BB de wedstrijdkalender beheren """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_OVERZICHT_MANAGER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ)

    @staticmethod
    def _maak_filter_knoppen(context, gekozen_status):
        """ filter knoppen voor de wedstrijdstatus """

        context['status_filters'] = status_filters = list()

        optie_alle = SimpleNamespace(
                            sel='status_alle',
                            beschrijving='Alle',
                            selected=True,              # fallback, kan verderop op False gezet worden
                            zoom_url=reverse('Wedstrijden:manager'))
        status_filters.append(optie_alle)

        for status, beschrijving in WEDSTRIJD_STATUS_CHOICES:       # gegarandeerde volgorde

            url_param = WEDSTRIJD_STATUS2URL[status]
            url = reverse('Wedstrijden:manager-status', kwargs={'status': url_param})
            selected = (status == gekozen_status)

            if selected:
                optie_alle.selected = False

            optie = SimpleNamespace(
                            sel='status_%s' % url_param,
                            beschrijving=beschrijving,
                            selected=selected,
                            zoom_url=url)

            status_filters.append(optie)
        # for

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            status_str = kwargs['status'][:15]          # afkappen voor de veiligheid
            status = WEDSTRIJD_URL2STATUS[status_str]
        except KeyError:
            status = None

        # begin 2 maanden terug in tijd (oudere wedstrijden zijn niet interessant)
        datum_vanaf = timezone.now().date() - datetime.timedelta(days=61)

        # pak de 50 meest recente wedstrijden
        wedstrijden = (Wedstrijd
                       .objects
                       .filter(datum_begin__gte=datum_vanaf,
                               verstop_voor_mwz=False)
                       .order_by('datum_begin'))

        if status:
            wedstrijden = wedstrijden.filter(status=status)

        wedstrijden = wedstrijden[:100]

        for wed in wedstrijden:
            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wed.organisatie]
            wed.disc_str = ORGANISATIES2SHORT_STR[wed.organisatie] + ' / ' + disc2str[wed.discipline]
            wed.status_str = WEDSTRIJD_STATUS_TO_STR[wed.status]
            wed.status_val_op = (wed.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING)
            wed.url_wijzig = reverse('Wedstrijden:wijzig-wedstrijd', kwargs={'wedstrijd_pk': wed.pk})
            wed.url_sessies = reverse('Wedstrijden:wijzig-sessies', kwargs={'wedstrijd_pk': wed.pk})

            if wed.eis_kwalificatie_scores:
                wed.url_check_kwalificatie_scores = reverse('Wedstrijden:check-kwalificatie-scores',
                                                            kwargs={'wedstrijd_pk': wed.pk})
        # for

        context['wedstrijden'] = wedstrijden

        context['huidige_rol'] = rol_get_beschrijving(request)

        self._maak_filter_knoppen(context, status)

        context['kruimels'] = (
            (None, 'Wedstrijdkalender'),
        )

        return render(request, self.template_name, context)


class ZetStatusWedstrijdView(UserPassesTestMixin, View):

    """ Via deze view kan de MWZ of HWL de wedstrijd status aanpassen """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_MWZ, Rollen.ROL_HWL)

    @staticmethod
    def _maak_taak_voor_bb(wedstrijd):
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_tekst = "Wedstrijd %s van vereniging %s is ingediend voor goedkeuring" % (
                        repr(wedstrijd.titel), wedstrijd.organiserende_vereniging)
        taak_tekst += '\n\nGa naar de Wedstrijdkalender om deze wedstrijd te behandelen.'
        taak_onderwerp = "Verzoek goedkeuring nieuwe wedstrijden"

        # maak een taak voor de Manager Wedstrijdzaken
        functie_mwz = Functie.objects.get(rol='MWZ')
        maak_taak(
            toegekend_aan_functie=functie_mwz,
            deadline=taak_deadline,
            onderwerp=taak_onderwerp,
            beschrijving=taak_tekst,
            log=taak_log)

    @staticmethod
    def _maak_taak_voor_hwl(wedstrijd, msg):
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_tekst = msg % repr(wedstrijd.titel)
        taak_tekst += '\n\nGa naar de Wedstrijdkalender om deze wedstrijd te behandelen.'
        taak_onderwerp = "Wedstrijdstatus is aangepast"

        # maak een taak aan voor de HWL van de organiserende vereniging
        functie_hwl = wedstrijd.organiserende_vereniging.functie_set.filter(rol='HWL').first()
        if functie_hwl:         # pragma: no branch
            maak_taak(
                toegekend_aan_functie=functie_hwl,
                deadline=taak_deadline,
                onderwerp=taak_onderwerp,
                beschrijving=taak_tekst,
                log=taak_log)

    @staticmethod
    def _maak_taak_voor_cs(wedstrijd):
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_tekst = "Wedstrijd %s is op de kalender gezet en heeft scheidsrechter(s) nodig.\n" % repr(wedstrijd.titel)
        taak_tekst += "Datum: %s" % wedstrijd.datum_begin
        if wedstrijd.datum_einde != wedstrijd.datum_begin:
            taak_tekst += "..%s" % wedstrijd.datum_einde
        taak_tekst += '\n'
        if wedstrijd.locatie:
            taak_tekst += "Locatie: %s" % wedstrijd.locatie.plaats
        taak_tekst += '\n\nGa naar Scheidsrechters, Wedstrijdkalender om deze wedstrijd te behandelen.'
        taak_tekst += '\n\n(wedstrijd nummer: %s)\n' % wedstrijd.pk
        taak_onderwerp = "Nieuwe wedstrijd op de kalender"

        # maak een taak aan voor de CS
        functie_cs = Functie.objects.get(rol='CS')
        maak_taak(
            toegekend_aan_functie=functie_cs,
            deadline=taak_deadline,
            onderwerp=taak_onderwerp,
            beschrijving=taak_tekst,
            log=taak_log)

    @staticmethod
    def _garandeer_betaalinstellingen_bestaat(ver):
        """ BetaalInstellingenVereniging is noodzakelijk voor een inschrijving,
            maar wordt pas aangemaakt als de vereniging het kaartje Financieel gebruikt.
            Omdat handmatige overschrijving nu ook kan, zorgen we hier dat het record bestaat.
        """
        _ = BetaalInstellingenVereniging.objects.get_or_create(vereniging=ver)

    def post(self, request, *args, **kwargs):

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .get(pk=wedstrijd_pk,
                              verstop_voor_mwz=False))
        except Wedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        terug = request.POST.get('terug', '')
        verder = request.POST.get('verder', '')
        annuleer = request.POST.get('annuleer', '')

        # FUTURE: zet wijzigingen in het logboek, of begin een logboekje per wedstrijd

        if self.rol_nu == Rollen.ROL_HWL:
            if wedstrijd.organiserende_vereniging != self.functie_nu.vereniging:
                raise PermissionDenied('Wedstrijd niet van jouw vereniging')

            next_url = reverse('Wedstrijden:vereniging')

            if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP and verder:
                self._garandeer_betaalinstellingen_bestaat(wedstrijd.organiserende_vereniging)

                if not wedstrijd.verkoopvoorwaarden_status_acceptatie:
                    raise Http404('Verkoopvoorwaarden')

                # verzoek tot goedkeuring
                wedstrijd.status = WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING
                wedstrijd.save(update_fields=['status'])
                # maak een taak aan voor de BB
                self._maak_taak_voor_bb(wedstrijd)

        else:
            next_url = reverse('Wedstrijden:manager')

            if annuleer:
                # annuleer deze wedstrijd
                wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
                wedstrijd.save(update_fields=['status'])

                # maak een taak aan voor de HWL
                self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geannuleerd")

            elif wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
                if verder:
                    wedstrijd.status = WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING
                    wedstrijd.save(update_fields=['status'])

            elif wedstrijd.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING:
                if terug:
                    # afgekeurd --> terug naar ontwerp
                    wedstrijd.status = WEDSTRIJD_STATUS_ONTWERP
                    wedstrijd.save(update_fields=['status'])

                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is terug gezet naar de status 'ontwerp'")

                elif verder:
                    # goedgekeurd --> naar geaccepteerd
                    wedstrijd.status = WEDSTRIJD_STATUS_GEACCEPTEERD
                    wedstrijd.save(update_fields=['status'])

                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geaccepteerd en openbaar")

                    if wedstrijd.aantal_scheids > 0:
                        # maak een taak voor de CS om scheidsrechters toe te kennen
                        self._maak_taak_voor_cs(wedstrijd)

        return HttpResponseRedirect(next_url)

# end of file
