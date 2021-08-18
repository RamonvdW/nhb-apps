# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_mag_wisselen
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid
from .models import SchutterVoorkeuren, SchutterBoog
import logging


TEMPLATE_VOORKEUREN = 'schutter/voorkeuren.dtl'
TEMPLATE_VOORKEUREN_OPGESLAGEN = 'schutter/voorkeuren-opgeslagen.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen schutters hun voorkeuren inzien en aanpassen """

    template_name = TEMPLATE_VOORKEUREN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SCHUTTER, Rollen.ROL_HWL)

    @staticmethod
    def _get_nhblid_or_404(request, nhblid_pk):
        """ Geeft het nhblid record terug van de schutter zelf,
            of in geval van de HWL de gekozen schutter """

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if rol_nu == Rollen.ROL_HWL:
            try:
                # conversie naar integer geef input-controle
                nhblid_pk = int(nhblid_pk)
            except (ValueError, TypeError):
                # nhblid_pk was geen getal
                raise Http404('Sporter niet gevonden')

            try:
                nhblid = NhbLid.objects.get(pk=nhblid_pk)
            except NhbLid.DoesNotExist:
                raise Http404('Sporter niet gevonden')

            # laatste control: het nhblid moet lid zijn bij de vereniging van de HWL
            if nhblid.bij_vereniging != functie_nu.nhb_ver:
                raise PermissionDenied('Geen sporter van jouw vereniging')

            return nhblid

        account = request.user
        nhblid = account.nhblid_set.all()[0]  # ROL_SCHUTTER geeft bescherming tegen geen nhblid

        return nhblid

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""

        nhblid = self._get_nhblid_or_404(request,
                                         request.POST.get('nhblid_pk', None))

        # sla de nieuwe voorkeuren op in SchutterBoog records (1 per boogtype)
        # werkt alleen na een GET (maakt de SchutterBoog records aan)
        for obj in (SchutterBoog
                    .objects
                    .filter(nhblid=nhblid)
                    .select_related('boogtype')):

            # wedstrijdboog
            old_voor_wedstrijd = obj.voor_wedstrijd
            obj.voor_wedstrijd = False
            if request.POST.get('schiet_' + obj.boogtype.afkorting, None):
                obj.voor_wedstrijd = True

            # informatie over de boog
            old_heeft_interesse = obj.heeft_interesse
            obj.heeft_interesse = False
            if request.POST.get('info_' + obj.boogtype.afkorting, None):
                obj.heeft_interesse = True

            if (old_voor_wedstrijd != obj.voor_wedstrijd or
                    old_heeft_interesse != obj.heeft_interesse):
                # wijzigingen opslaan
                obj.save()
        # for

        voorkeuren, _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)

        old_eigen_blazoen = voorkeuren.voorkeur_eigen_blazoen
        voorkeuren.voorkeur_eigen_blazoen = False
        if request.POST.get('voorkeur_eigen_blazoen', None):
            voorkeuren.voorkeur_eigen_blazoen = True

        old_voorkeur_meedoen_competitie = voorkeuren.voorkeur_meedoen_competitie
        voorkeuren.voorkeur_meedoen_competitie = False
        if request.POST.get('voorkeur_meedoen_competitie', None):
            voorkeuren.voorkeur_meedoen_competitie = True

        if (old_voorkeur_meedoen_competitie != voorkeuren.voorkeur_meedoen_competitie or
                old_eigen_blazoen != voorkeuren.voorkeur_eigen_blazoen):
            # wijzigingen opslaan
            voorkeuren.save(update_fields=['voorkeur_eigen_blazoen', 'voorkeur_meedoen_competitie'])

        if nhblid.para_classificatie:
            para_notitie = request.POST.get('para_notitie', '')
            if para_notitie != voorkeuren.opmerking_para_sporter:
                # wijziging opslaan
                voorkeuren.opmerking_para_sporter = para_notitie
                voorkeuren.save(update_fields=['opmerking_para_sporter'])

        old_disc_outdoor = voorkeuren.voorkeur_discipline_outdoor
        voorkeuren.voorkeur_discipline_outdoor = False
        if request.POST.get('voorkeur_disc_outdoor', None):
            voorkeuren.voorkeur_discipline_outdoor = True

        old_disc_indoor = voorkeuren.voorkeur_discipline_indoor
        voorkeuren.voorkeur_discipline_indoor = False
        if request.POST.get('voorkeur_disc_indoor', None):
            voorkeuren.voorkeur_discipline_indoor = True

        old_disc_25m1p = voorkeuren.voorkeur_discipline_25m1pijl
        voorkeuren.voorkeur_discipline_25m1pijl = False
        if request.POST.get('voorkeur_disc_25m1p', None):
            voorkeuren.voorkeur_discipline_25m1pijl = True

        old_disc_clout = voorkeuren.voorkeur_discipline_clout
        voorkeuren.voorkeur_discipline_clout = False
        if request.POST.get('voorkeur_disc_clout', None):
            voorkeuren.voorkeur_discipline_clout = True

        old_disc_veld = voorkeuren.voorkeur_discipline_veld
        voorkeuren.voorkeur_discipline_veld = False
        if request.POST.get('voorkeur_disc_veld', None):
            voorkeuren.voorkeur_discipline_veld = True

        old_disc_run = voorkeuren.voorkeur_discipline_run
        voorkeuren.voorkeur_discipline_run = False
        if request.POST.get('voorkeur_disc_run', None):
            voorkeuren.voorkeur_discipline_run = True

        old_disc_3d = voorkeuren.voorkeur_discipline_3d
        voorkeuren.voorkeur_discipline_3d = False
        if request.POST.get('voorkeur_disc_3d', None):
            voorkeuren.voorkeur_discipline_3d = True

        if (old_disc_outdoor != voorkeuren.voorkeur_discipline_outdoor or
                old_disc_indoor != voorkeuren.voorkeur_discipline_indoor or
                old_disc_25m1p != voorkeuren.voorkeur_discipline_25m1pijl or
                old_disc_clout != voorkeuren.voorkeur_discipline_clout or
                old_disc_veld != voorkeuren.voorkeur_discipline_veld or
                old_disc_run != voorkeuren.voorkeur_discipline_run or
                old_disc_3d != voorkeuren.voorkeur_discipline_3d):
            # wijzigingen opslaan
            voorkeuren.save(update_fields=['voorkeur_discipline_25m1pijl',
                                           'voorkeur_discipline_outdoor',
                                           'voorkeur_discipline_indoor',
                                           'voorkeur_discipline_clout',
                                           'voorkeur_discipline_veld',
                                           'voorkeur_discipline_run',
                                           'voorkeur_discipline_3d'])

        del voorkeuren

        if self.rol_nu != Rollen.ROL_HWL:
            if rol_mag_wisselen(self.request):
                account = request.user
                email = account.accountemail_set.all()[0]
                updated = list()

                optout_nieuwe_taak = False
                if request.POST.get('optout_nieuwe_taak'):
                    optout_nieuwe_taak = True
                if email.optout_nieuwe_taak != optout_nieuwe_taak:
                    # wijziging doorvoeren
                    email.optout_nieuwe_taak = optout_nieuwe_taak
                    updated.append('optout_nieuwe_taak')

                optout_herinnering_taken = False
                if request.POST.get('optout_herinnering_taken'):
                    optout_herinnering_taken = True

                if email.optout_herinnering_taken != optout_herinnering_taken:
                    # wijziging doorvoeren
                    email.optout_herinnering_taken = optout_herinnering_taken
                    updated.append('optout_herinnering_taken')

                # wijziging opslaan
                if len(updated):
                    email.save(update_fields=updated)

        if self.rol_nu == Rollen.ROL_HWL:
            # stuur de HWL terug naar zijn ledenlijst
            return HttpResponseRedirect(reverse('Vereniging:leden-voorkeuren'))

        return HttpResponseRedirect(reverse('Schutter:profiel'))

    @staticmethod
    def _get_bogen(nhblid, geen_wedstrijden):
        """ Retourneer een lijst met SchutterBoog objecten, aangevuld met hulpvelden """

        if geen_wedstrijden:
            # schutter mag niet aan wedstrijden deelnemen
            # verwijder daarom alle SchutterBoog records
            SchutterBoog.objects.filter(nhblid=nhblid).delete()
            return None

        # haal de SchutterBoog records op van deze gebruiker
        objs = (SchutterBoog
                .objects
                .filter(nhblid=nhblid)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # maak ontbrekende SchutterBoog records aan, indien nodig
        boogtypen = BoogType.objects.all()
        if len(objs) < len(boogtypen):
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                schutterboog = SchutterBoog()
                schutterboog.nhblid = nhblid
                schutterboog.boogtype = boogtype
                schutterboog.save()
            # for
            objs = (SchutterBoog
                    .objects
                    .filter(nhblid=nhblid)
                    .select_related('boogtype')
                    .order_by('boogtype__volgorde'))

        # voeg de checkbox velden toe
        for obj in objs:
            obj.check_schiet = 'schiet_' + obj.boogtype.afkorting
            obj.check_info = 'info_' + obj.boogtype.afkorting
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            nhblid_pk = kwargs['nhblid_pk']
        except KeyError:
            nhblid_pk = None
        nhblid = self._get_nhblid_or_404(self.request, nhblid_pk)

        context['geen_wedstrijden'] = geen_wedstrijden = nhblid.bij_vereniging and nhblid.bij_vereniging.geen_wedstrijden

        context['bogen'] = self._get_bogen(nhblid, geen_wedstrijden)
        context['voorkeuren'], _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)
        context['nhblid'] = nhblid

        if self.rol_nu == Rollen.ROL_HWL:
            actief = 'vereniging'
            context['nhblid_pk'] = nhblid.pk
            context['is_hwl'] = True
        else:
            # niet de HWL maar de schutter zelf
            actief = 'schutter-profiel'
            if rol_mag_wisselen(self.request):
                # schutter is beheerder, dus toon opt-out opties
                context['email'] = nhblid.account.accountemail_set.all()[0]

        context['opslaan_url'] = reverse('Schutter:voorkeuren')

        menu_dynamics(self.request, context, actief=actief)
        return context


# end of file
