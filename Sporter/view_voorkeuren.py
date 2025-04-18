# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import (GESLACHT_MAN, GESLACHT_VROUW, GESLACHT_ANDERS, GESLACHT_MV_MEERVOUD,
                                   ORGANISATIE_IFAA, SCHEIDS_NIET)
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_mag_wisselen
from Sporter.models import Sporter, get_sporter
from Sporter.operations import get_sporter_voorkeuren, get_sporterboog
from types import SimpleNamespace
import logging


TEMPLATE_VOORKEUREN = 'sporter/voorkeuren.dtl'

my_logger = logging.getLogger('MH.Sporter')


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen sporters hun voorkeuren inzien en aanpassen
        Ook de SEC en HWL kunnen via deze view de instellingen van een lid van de vereniging aanpassen
    """

    template_name = TEMPLATE_VOORKEUREN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None
        self.functie_nu = None
        self.sporter = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en de rol Sporter gekozen hebben
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_SPORTER, Rol.ROL_SEC, Rol.ROL_HWL)

    def _get_sporter_or_404(self, sporter_pk):
        """ Geeft het Sporter record terug van de sporter zelf,
            of in geval van de HWL de gekozen sporter """

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
            try:
                # conversie naar integer geef input-controle
                sporter_pk = int(sporter_pk)
            except (ValueError, TypeError):
                # sporter_pk was geen getal
                raise Http404('Sporter niet gevonden')

            try:
                self.sporter = Sporter.objects.select_related('bij_vereniging', 'account').get(pk=sporter_pk)
            except Sporter.DoesNotExist:
                raise Http404('Sporter niet gevonden')

            # laatste control: de sporter moet lid zijn bij de vereniging van de HWL
            if self.sporter.bij_vereniging != self.functie_nu.vereniging:
                raise PermissionDenied('Geen sporter van jouw vereniging')

        else:
            # fallback naar ingelogde gebruiker
            account = get_account(self.request)
            # ROL_SPORTER geeft bescherming tegen geen sporter
            self.sporter = get_sporter(account)

    def _update_sporterboog(self):
        objs = get_sporterboog(self.sporter, mag_database_wijzigen=True)

        # voer de wijzigingen door
        for obj in objs:
            # wedstrijdboog
            old_voor_wedstrijd = obj.voor_wedstrijd
            obj.voor_wedstrijd = False
            if self.request.POST.get('schiet_' + obj.boogtype.afkorting, None):
                obj.voor_wedstrijd = True

            # informatie over de boog
            old_heeft_interesse = obj.heeft_interesse
            obj.heeft_interesse = False
            if self.request.POST.get('info_' + obj.boogtype.afkorting, None):
                obj.heeft_interesse = True

            if (old_voor_wedstrijd != obj.voor_wedstrijd or
                    old_heeft_interesse != obj.heeft_interesse):
                # wijzigingen opslaan
                obj.save(update_fields=['heeft_interesse', 'voor_wedstrijd'])
        # for

    def _update_voorkeuren(self, is_beheerder):
        voorkeuren = get_sporter_voorkeuren(self.sporter, mag_database_wijzigen=True)

        keuze = self.request.POST.get('voorkeur_eigen_blazoen', None) is not None
        voorkeuren.voorkeur_eigen_blazoen = keuze

        keuze = self.request.POST.get('voorkeur_meedoen_competitie', None) is not None
        voorkeuren.voorkeur_meedoen_competitie = keuze

        para_notitie = self.request.POST.get('para_notitie', '')
        voorkeuren.opmerking_para_sporter = para_notitie

        keuze = self.request.POST.get('para_voorwerpen', None) is not None
        voorkeuren.para_voorwerpen = keuze

        keuze = self.request.POST.get('voorkeur_disc_outdoor', None) is not None
        voorkeuren.voorkeur_discipline_outdoor = keuze

        keuze = self.request.POST.get('voorkeur_disc_indoor', None) is not None
        voorkeuren.voorkeur_discipline_indoor = keuze

        keuze = self.request.POST.get('voorkeur_disc_25m1p', None) is not None
        voorkeuren.voorkeur_discipline_25m1pijl = keuze

        keuze = self.request.POST.get('voorkeur_disc_clout', None) is not None
        voorkeuren.voorkeur_discipline_clout = keuze

        keuze = self.request.POST.get('voorkeur_disc_veld', None) is not None
        voorkeuren.voorkeur_discipline_veld = keuze

        keuze = self.request.POST.get('voorkeur_disc_run', None) is not None
        voorkeuren.voorkeur_discipline_run = keuze

        keuze = self.request.POST.get('voorkeur_disc_3d', None) is not None
        voorkeuren.voorkeur_discipline_3d = keuze

        if self.sporter.geslacht == GESLACHT_ANDERS:
            keuze = self.request.POST.get('wedstrijd_mv', None)

            if keuze in (GESLACHT_MAN, GESLACHT_VROUW):
                gekozen = True
            else:
                # veld accepteert alleen man of vrouw
                keuze = GESLACHT_MAN
                gekozen = False

            voorkeuren.wedstrijd_geslacht_gekozen = gekozen
            voorkeuren.wedstrijd_geslacht = keuze

        if not is_beheerder:
            # alleen de sporter zelf mag dit bepalen
            keuze = self.request.POST.get('sr_korps_email', None) is not None
            voorkeuren.scheids_opt_in_korps_email = keuze

            keuze = self.request.POST.get('sr_korps_tel', None) is not None
            voorkeuren.scheids_opt_in_korps_tel_nr = keuze

            keuze = self.request.POST.get('sr_wed_email', None) is not None
            voorkeuren.scheids_opt_in_ver_email = keuze

            keuze = self.request.POST.get('sr_wed_tel', None) is not None
            voorkeuren.scheids_opt_in_ver_tel_nr = keuze

        voorkeuren.save()

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""

        self._get_sporter_or_404(request.POST.get('sporter_pk', None))

        is_beheerder = self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL)

        self._update_sporterboog()
        self._update_voorkeuren(is_beheerder)

        if is_beheerder:
            # stuur de beheerder terug naar zijn ledenlijst
            return HttpResponseRedirect(reverse('Vereniging:leden-voorkeuren'))

        # sporter
        if rol_mag_wisselen(self.request):
            account = get_account(request)
            updated = list()

            optout_nieuwe_taak = False
            if request.POST.get('optout_nieuwe_taak'):
                optout_nieuwe_taak = True
            if account.optout_nieuwe_taak != optout_nieuwe_taak:
                # wijziging doorvoeren
                account.optout_nieuwe_taak = optout_nieuwe_taak
                updated.append('optout_nieuwe_taak')

            optout_herinnering_taken = False
            if request.POST.get('optout_herinnering_taken'):
                optout_herinnering_taken = True

            if account.optout_herinnering_taken != optout_herinnering_taken:
                # wijziging doorvoeren
                account.optout_herinnering_taken = optout_herinnering_taken
                updated.append('optout_herinnering_taken')

            # wijziging opslaan
            if len(updated):
                account.save(update_fields=updated)

        return HttpResponseRedirect(reverse('Sporter:profiel'))

    def _get_bogen(self, geen_wedstrijden):
        """ Retourneer een lijst met SporterBoog objecten, aangevuld met hulpvelden """

        if geen_wedstrijden:
            # sporter mag niet aan wedstrijden deelnemen
            return None, None

        objs = get_sporterboog(self.sporter, mag_database_wijzigen=False, geen_wedstrijden=geen_wedstrijden)

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
        self._get_sporter_or_404(sporter_pk)

        context['sporter'] = self.sporter
        context['voorkeuren'] = voorkeuren = get_sporter_voorkeuren(self.sporter)

        geen_wedstrijden = self.sporter.bij_vereniging and self.sporter.bij_vereniging.geen_wedstrijden
        context['geen_wedstrijden'] = geen_wedstrijden

        context['bogen_wa'], context['bogen_ifaa'] = self._get_bogen(geen_wedstrijden)

        if self.sporter.geslacht == GESLACHT_ANDERS:
            context['toon_geslacht'] = True
            context['opt_wedstrijd_mv'] = opts = list()

            opt = SimpleNamespace(sel='X', tekst='Geen keuze', selected=not voorkeuren.wedstrijd_geslacht_gekozen)
            opts.append(opt)

            for sel, tekst in GESLACHT_MV_MEERVOUD:
                selected = (voorkeuren.wedstrijd_geslacht_gekozen and voorkeuren.wedstrijd_geslacht == sel)
                opt = SimpleNamespace(sel=sel, tekst=tekst, selected=selected)
                opts.append(opt)
            # for

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
            context['sporter_pk'] = self.sporter.pk
            context['is_hwl'] = True
            context['toon_contact_sr'] = False      # delen contactgegevens is aan de sporter, niet de HWL
        else:
            # niet de HWL, dus de sporter zelf
            if rol_mag_wisselen(self.request):
                # sporter is beheerder, dus toon opt-out opties
                context['account'] = self.sporter.account

            context['toon_contact_sr'] = self.sporter.scheids != SCHEIDS_NIET

        context['toon_bondscompetities'] = not self.sporter.is_gast
        context['opslaan_url'] = reverse('Sporter:voorkeuren')

        if self.rol_nu in (Rol.ROL_SEC, Rol.ROL_HWL):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Vereniging:leden-voorkeuren'), 'Voorkeuren leden'),
                (None, 'Voorkeuren')
            )
        else:
            context['kruimels'] = (
                (reverse('Sporter:profiel'), 'Mijn pagina'),
                (None, 'Voorkeuren')
            )

        return context


# end of file
