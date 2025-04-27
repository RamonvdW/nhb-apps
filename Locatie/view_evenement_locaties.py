# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Locatie.models import EvenementLocatie
from Logboek.models import schrijf_in_logboek
from Vereniging.models import Vereniging


TEMPLATE_EVENEMENT_LOCATIE = 'locatie/evenement-locaties.dtl'
TEMPLATE_EVENEMENT_LOCATIE_DETAILS = 'locatie/evenement-locatie-details.dtl'


class EvenementLocatiesView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een externe locatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_LOCATIE
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MO, Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC)

    def get_vereniging_or_404(self):
        try:
            ver_nr = int(self.kwargs['ver_nr'][:6])        # afkappen voor de veiligheid
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except (ValueError, Vereniging.DoesNotExist):
            raise Http404('Vereniging niet gevonden')

        if ver.ver_nr not in (settings.EVENEMENTEN_VERKOPER_VER_NRS + settings.OPLEIDINGEN_VERKOPER_VER_NRS):
            raise PermissionDenied('Geen toegang')

        if self.functie_nu and self.functie_nu.vereniging:
            if self.functie_nu.vereniging.ver_nr != ver.ver_nr:
                raise Http404('Niet de beheerder')

        return ver

    def _bepaal_readonly(self):
        # MO mag wijzigen
        if self.rol_nu == Rol.ROL_MO:
            return False

        # HWL mag wijzigen
        if self.functie_nu and self.functie_nu.rol == 'HWL':
            return False

        # de rest mag niet wijzigen
        return True

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = ver = self.get_vereniging_or_404()

        context['readonly'] = readonly = self._bepaal_readonly()
        if not readonly:
            context['url_toevoegen'] = reverse('Locatie:evenement-locaties',
                                               kwargs={'ver_nr': ver.ver_nr})

        locaties = ver.evenementlocatie_set.filter(zichtbaar=True)
        context['locaties'] = locaties

        for locatie in locaties:
            locatie.geen_naam = locatie.naam.strip() == ""
            locatie.geen_plaats = locatie.plaats.strip() == ""

            locatie.url_wijzig = reverse('Locatie:evenement-locatie-details',
                                         kwargs={'ver_nr': ver.ver_nr,
                                                 'locatie_pk': locatie.pk})
        # for

        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (None, 'Evenement locaties')
            )
        else:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (None, 'Evenement locaties')
            )

        return context

    def post(self, request, *args, **kwargs):
        """ maak een nieuwe evenement locatie aan """

        ver = self.get_vereniging_or_404()

        if self._bepaal_readonly():
            raise PermissionDenied('Geen toegang')

        locatie = EvenementLocatie(vereniging=ver)
        locatie.save()

        # meteen wijzigen
        url = reverse('Locatie:evenement-locatie-details',
                      kwargs={'ver_nr': ver.ver_nr,
                              'locatie_pk': locatie.pk})

        return HttpResponseRedirect(url)


class EvenementLocatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een locatie aangepast worden.
        Alleen de HWL van de vereniging(en) die aan deze locatie gekoppeld zijn mogen de details aanpassen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_LOCATIE_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MO,
                               Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC)

    def get_locatie(self, ver: Vereniging):
        """ haal de locatie op en geef een 404 als deze niet bestaat
            doe een access-check en
        """
        try:
            location_pk = int(self.kwargs['locatie_pk'][:6])        # afkappen voor de veiligheid
            locatie = EvenementLocatie.objects.get(pk=location_pk,
                                                   vereniging=ver,
                                                   zichtbaar=True)
        except (ValueError, EvenementLocatie.DoesNotExist):
            raise Http404('Locatie bestaat niet')

        return locatie

    def get_vereniging_or_404(self):
        try:
            ver_nr = int(self.kwargs['ver_nr'][:6])          # afkappen voor de veiligheid
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except (ValueError, Vereniging.DoesNotExist):
            raise Http404('Vereniging niet gevonden')

        if ver.ver_nr not in (settings.EVENEMENTEN_VERKOPER_VER_NRS + settings.OPLEIDINGEN_VERKOPER_VER_NRS):
            raise PermissionDenied('Geen toegang')

        if self.functie_nu and self.functie_nu.vereniging:
            if self.functie_nu.vereniging.ver_nr != ver.ver_nr:
                raise Http404('Niet de beheerder')

        return ver

    def _bepaal_readonly(self):
        # MO mag wijzigen
        if self.rol_nu == Rol.ROL_MO:
            return False

        # HWL mag wijzigen
        if self.functie_nu and self.functie_nu.rol == 'HWL':
            return False

        # de rest mag niet wijzigen
        return True

    @staticmethod
    def _get_gebruik(locatie) -> (list, list):
        gebruik_evenement = list()
        for evenement in locatie.evenement_set.all():
            gebruik_evenement.append(evenement)
        # for

        gebruik_opleiding = list()
        for moment in locatie.opleidingmoment_set.all():
            for opleiding in moment.opleiding_set.all():
                gebruik_opleiding.append(opleiding)
            # for
        # for

        is_used = len(gebruik_evenement) + len(gebruik_opleiding) > 0

        return gebruik_evenement, gebruik_opleiding, is_used

    def get(self, request, *args, **kwargs):
        context = dict()
        context['ver'] = ver = self.get_vereniging_or_404()

        context['locatie'] = locatie = self.get_locatie(ver)
        context['rol'] = rol_get_beschrijving(self.request)

        context['gebruik_evenement'], context['gebruik_opleiding'], is_used = self._get_gebruik(locatie)

        context['readonly'] = readonly = self._bepaal_readonly()
        if not readonly:
            url = reverse('Locatie:evenement-locatie-details',
                          kwargs={'ver_nr': ver.ver_nr,
                                  'locatie_pk': locatie.pk})

            context['url_opslaan'] = url

            if not is_used:
                context['url_verwijder'] = url

        context['url_terug'] = reverse('Locatie:evenement-locaties',
                                       kwargs={'ver_nr': ver.ver_nr})

        if self.rol_nu == Rol.ROL_MO:
            context['kruimels'] = (
                (reverse('Opleiding:manager'), 'Opleidingen'),
                (reverse('Locatie:evenement-locaties', kwargs={'ver_nr': ver.ver_nr}), 'Evenement locaties'),
                (None, 'Locatie details')
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Locatie:evenement-locaties', kwargs={'ver_nr': ver.ver_nr}), 'Evenement locaties'),
                (None, 'Locatie details')
            )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        ver = self.get_vereniging_or_404()
        locatie = self.get_locatie(ver)

        if self.rol_nu not in (Rol.ROL_HWL, Rol.ROL_MO):
            raise PermissionDenied('Wijzigen alleen door HWL en MO')

        door_account = get_account(request)

        if request.POST.get('verwijder', ''):
            # controleer dat de locatie niet in gebruik is
            _, _, is_used = self._get_gebruik(locatie)
            if is_used:
                raise Http404('Nog in gebruik')

            # maak onzichtbaar in plaats van verwijderen
            locatie.zichtbaar = False
            locatie.save(update_fields=['zichtbaar'])

            # terug naar de overzichtspagina
            url = reverse('Locatie:evenement-locaties', kwargs={'ver_nr': ver.ver_nr})
            return HttpResponseRedirect(url)

        data = request.POST.get('naam', '')
        data = data[:50]    # afkappen voor de veiligheid + voorkom database fout bij opslaan
        if locatie.naam != data:
            activiteit = "Aanpassing naam externe locatie van vereniging %s: %s (was %s)" % (
                            ver, repr(data), repr(locatie.naam))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.naam = data

        data = request.POST.get('adres', '')
        data = data.replace('\r\n', '\n')
        data = data[:1000]      # afkappen voor de veiligheid
        if locatie.adres != data:
            activiteit = "Aanpassing adres van externe locatie %s van vereniging %s: %s (was %s)" % (
                            locatie.naam, ver,
                            repr(data.replace('\n', ', ')),
                            repr(locatie.adres.replace('\n', ', ')))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.adres = data
            # zorg dat de lat/lon opnieuw vastgesteld gaat worden
            locatie.adres_lat = ''
            locatie.adres_lon = ''

        data = request.POST.get('plaats', '')
        data = data[:50]    # afkappen voor de veiligheid + voorkom database fout bij opslaan
        if locatie.plaats != data:
            activiteit = "Aanpassing plaats van externe locatie %s van vereniging %s: %s (was %s)" % (
                            locatie.naam, ver,
                            repr(data),
                            repr(locatie.plaats))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.plaats = data

        data = request.POST.get('notities', '')
        data = data.replace('\r\n', '\n')
        data = data[:1000]      # afkappen voor de veiligheid
        if locatie.notities != data:
            activiteit = "Aanpassing bijzonderheden van externe locatie %s" % locatie.naam
            activiteit += " van vereniging %s: %s (was %s)" % (
                            ver,
                            repr(data.replace('\n', ' / ')),
                            repr(locatie.notities.replace('\n', ' / ')))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.notities = data

        locatie.save()

        url = reverse('Locatie:evenement-locaties',
                      kwargs={'ver_nr': ver.ver_nr})
        return HttpResponseRedirect(url)


# end of file
