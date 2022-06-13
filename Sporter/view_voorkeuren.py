# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import (BoogType,
                               GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ANDERS,
                               GESLACHT_MV_MEERVOUD, ORGANISATIE_IFAA)
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_mag_wisselen
from Plein.menu import menu_dynamics
from .models import Sporter, SporterBoog, get_sporter_voorkeuren
from types import SimpleNamespace
import logging


TEMPLATE_VOORKEUREN = 'sporter/voorkeuren.dtl'

my_logger = logging.getLogger('NHBApps.Sporter')


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen sporters hun voorkeuren inzien en aanpassen """

    template_name = TEMPLATE_VOORKEUREN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en de rol Sporter gekozen hebben
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_SPORTER, Rollen.ROL_HWL)

    @staticmethod
    def _get_sporter_or_404(request, sporter_pk):
        """ Geeft het Sporter record terug van de sporter zelf,
            of in geval van de HWL de gekozen sporter """

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if rol_nu == Rollen.ROL_HWL:
            try:
                # conversie naar integer geef input-controle
                sporter_pk = int(sporter_pk)
            except (ValueError, TypeError):
                # sporter_pk was geen getal
                raise Http404('Sporter niet gevonden')

            try:
                sporter = Sporter.objects.get(pk=sporter_pk)
            except Sporter.DoesNotExist:
                raise Http404('Sporter niet gevonden')

            # laatste control: de sporter moet lid zijn bij de vereniging van de HWL
            if sporter.bij_vereniging != functie_nu.nhb_ver:
                raise PermissionDenied('Geen sporter van jouw vereniging')

            return sporter

        account = request.user
        sporter = account.sporter_set.all()[0]  # ROL_SPORTER geeft bescherming tegen geen sporter

        return sporter

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""

        sporter = self._get_sporter_or_404(request,
                                           request.POST.get('sporter_pk', None))

        # sla de nieuwe voorkeuren op in SporterBoog records (1 per boogtype)
        # werkt alleen na een GET (maakt de SporterBoog records aan)
        for obj in (SporterBoog
                    .objects
                    .filter(sporter=sporter)
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
                obj.save(update_fields=['heeft_interesse', 'voor_wedstrijd'])
        # for

        voorkeuren = get_sporter_voorkeuren(sporter)

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

        para_notitie = request.POST.get('para_notitie', '')
        if para_notitie != voorkeuren.opmerking_para_sporter:
            # wijziging opslaan
            voorkeuren.opmerking_para_sporter = para_notitie
            voorkeuren.save(update_fields=['opmerking_para_sporter'])

        old_voorkeur_para_met_rolstoel = voorkeuren.para_met_rolstoel
        voorkeuren.para_met_rolstoel = False
        if request.POST.get('para_rolstoel', None):
            voorkeuren.para_met_rolstoel = True
        if old_voorkeur_para_met_rolstoel != voorkeuren.para_met_rolstoel:
            # wijziging opslaan
            voorkeuren.save(update_fields=['para_met_rolstoel'])

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

        if sporter.geslacht == GESLACHT_ANDERS:
            keuze = request.POST.get('wedstrijd_mv', None)

            if keuze in (GESLACHT_MAN, GESLACHT_VROUW):
                gekozen = True
            else:
                # veld accepteert alleen man of vrouw
                keuze = GESLACHT_MAN
                gekozen = False

            if gekozen != voorkeuren.wedstrijd_geslacht_gekozen or voorkeuren.wedstrijd_geslacht != keuze:
                voorkeuren.wedstrijd_geslacht_gekozen = gekozen
                voorkeuren.wedstrijd_geslacht = keuze
                voorkeuren.save(update_fields=['wedstrijd_geslacht_gekozen', 'wedstrijd_geslacht'])

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

        return HttpResponseRedirect(reverse('Sporter:profiel'))

    @staticmethod
    def _get_bogen(sporter, geen_wedstrijden):
        """ Retourneer een lijst met SporterBoog objecten, aangevuld met hulpvelden """

        if geen_wedstrijden:
            # sporter mag niet aan wedstrijden deelnemen
            # verwijder daarom alle SporterBoog records
            SporterBoog.objects.filter(sporter=sporter).delete()
            return None, None

        # haal de SporterBoog records op van deze gebruiker
        objs = (SporterBoog
                .objects
                .filter(sporter=sporter)
                .select_related('boogtype')
                .order_by('boogtype__volgorde'))

        # maak ontbrekende SporterBoog records aan, indien nodig
        boogtypen = BoogType.objects.exclude(buiten_gebruik=True)
        if len(objs) < len(boogtypen):
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            bulk = list()
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                sporterboog = SporterBoog(
                                    sporter=sporter,
                                    boogtype=boogtype)
                bulk.append(sporterboog)
            # for
            SporterBoog.objects.bulk_create(bulk)
            del bulk

            objs = (SporterBoog
                    .objects
                    .filter(sporter=sporter)
                    .select_related('boogtype')
                    .order_by('boogtype__volgorde'))

        # voeg de checkbox velden toe en opsplitsen in WA/IFAA
        objs_wa = list()
        objs_ifaa = list()
        for obj in objs:
            obj.check_schiet = 'schiet_' + obj.boogtype.afkorting
            obj.check_info = 'info_' + obj.boogtype.afkorting

            if obj.boogtype.organisatie == ORGANISATIE_IFAA:
                objs_ifaa.append(obj)
            else:
                objs_wa.append(obj)
        # for

        return objs_wa, objs_ifaa

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            sporter_pk = kwargs['sporter_pk']
        except KeyError:
            sporter_pk = None
        sporter = self._get_sporter_or_404(self.request, sporter_pk)

        context['geen_wedstrijden'] = geen_wedstrijden = sporter.bij_vereniging and sporter.bij_vereniging.geen_wedstrijden

        context['bogen_wa'], context['bogen_ifaa'] = self._get_bogen(sporter, geen_wedstrijden)
        context['sporter'] = sporter
        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(sporter)

        if sporter.geslacht == GESLACHT_ANDERS:
            context['toon_geslacht'] = True
            context['opt_wedstrijd_mv'] = opts = list()

            opt = SimpleNamespace(sel='X', tekst='Geen keuze', selected=not voorkeuren.wedstrijd_geslacht_gekozen)
            opts.append(opt)

            for sel, tekst in GESLACHT_MV_MEERVOUD:
                selected = (voorkeuren.wedstrijd_geslacht_gekozen and voorkeuren.wedstrijd_geslacht == sel)
                opt = SimpleNamespace(sel=sel, tekst=tekst, selected=selected)
                opts.append(opt)
            # for

        if self.rol_nu == Rollen.ROL_HWL:
            actief = 'vereniging'
            context['sporter_pk'] = sporter.pk
            context['is_hwl'] = True
        else:
            # niet de HWL maar de sporter zelf
            actief = 'sporter-profiel'
            if rol_mag_wisselen(self.request):
                # sporter is beheerder, dus toon opt-out opties
                context['email'] = sporter.account.accountemail_set.all()[0]

        context['opslaan_url'] = reverse('Sporter:voorkeuren')

        if self.rol_nu == Rollen.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (reverse('Vereniging:leden-voorkeuren'), 'Voorkeuren leden'),
                (None, 'Voorkeuren')
            )
        else:
            context['kruimels'] = (
                (reverse('Sporter:profiel'), 'Mijn pagina'),
                (None, 'Voorkeuren')
            )

        menu_dynamics(self.request, context)
        return context


# end of file
