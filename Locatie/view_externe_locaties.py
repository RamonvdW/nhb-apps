# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Locatie.models import WedstrijdLocatie
from Logboek.models import schrijf_in_logboek
from Vereniging.models import Vereniging


TEMPLATE_EXTERNE_LOCATIE = 'locatie/externe-locaties.dtl'
TEMPLATE_EXTERNE_LOCATIE_DETAILS = 'locatie/externe-locatie-details.dtl'


class ExterneLocatiesView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een externe locatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_EXTERNE_LOCATIE
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        # TODO: BB, BKO, RKO hebben geen link naar deze pagina. RCL alleen naar accommodatie pagina.
        return self.rol_nu in (Rol.ROL_BB,
                               Rol.ROL_BKO, Rol.ROL_RKO, Rol.ROL_RCL,
                               Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC)

    def get_vereniging(self):
        try:
            ver_nr = int(self.kwargs['ver_nr'][:6])        # afkappen voor de veiligheid
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except (ValueError, Vereniging.DoesNotExist):
            raise Http404('Vereniging niet gevonden')

        return ver

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['ver'] = ver = self.get_vereniging()

        context['readonly'] = True
        if self.functie_nu and self.functie_nu.rol == 'HWL' and self.functie_nu.vereniging == ver:
            context['readonly'] = False
            context['url_toevoegen'] = reverse('Locatie:externe-locaties',
                                               kwargs={'ver_nr': ver.ver_nr})

        locaties = ver.wedstrijdlocatie_set.filter(zichtbaar=True,
                                          baan_type='E')
        context['locaties'] = locaties

        for locatie in locaties:
            locatie.geen_naam = locatie.naam.strip() == ""
            locatie.geen_plaats = locatie.plaats.strip() == ""
            locatie.geen_disciplines = locatie.disciplines_str() == ""

            locatie.url_wijzig = reverse('Locatie:extern-locatie-details',
                                         kwargs={'ver_nr': ver.ver_nr,
                                                 'locatie_pk': locatie.pk})
        # for

        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC):
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
                (None, 'Locaties')
            )
        else:
            context['kruimels'] = (
                (reverse('Vereniging:lijst'), 'Verenigingen'),
                (None, 'Locaties')
            )

        return context

    def post(self, request, *args, **kwargs):
        """ maak een nieuwe externe locatie aan """

        ver = self.get_vereniging()

        if not self.functie_nu or self.functie_nu.rol != 'HWL' or self.functie_nu.vereniging != ver:
            raise PermissionDenied('Alleen HWL mag een locatie toevoegen')

        locatie = WedstrijdLocatie(baan_type='E')      # externe locatie
        locatie.save()
        locatie.verenigingen.add(ver)

        # meteen wijzigen
        url = reverse('Locatie:extern-locatie-details',
                      kwargs={'ver_nr': ver.ver_nr,
                              'locatie_pk': locatie.pk})

        return HttpResponseRedirect(url)


class ExterneLocatieDetailsView(TemplateView):

    """ Via deze view kunnen details van een locatie aangepast worden.
        Alleen de HWL van de vereniging(en) die aan deze locatie gekoppeld zijn mogen de details aanpassen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_EXTERNE_LOCATIE_DETAILS

    def get_locatie(self):
        """ haal de locatie op en geef een 404 als deze niet bestaat
            doe een access-check en
        """
        try:
            location_pk = int(self.kwargs['locatie_pk'][:6])        # afkappen voor de veiligheid
            locatie = WedstrijdLocatie.objects.get(pk=location_pk,
                                                   zichtbaar=True,
                                                   baan_type='E')   # voorkomt wijzigen accommodatie
        except (ValueError, WedstrijdLocatie.DoesNotExist):
            raise Http404('Locatie bestaat niet')

        return locatie

    def get_vereniging(self):
        try:
            ver_nr = int(self.kwargs['ver_nr'][:6])          # afkappen voor de veiligheid
            ver = Vereniging.objects.get(ver_nr=ver_nr)
        except (ValueError, Vereniging.DoesNotExist):
            raise Http404('Vereniging niet gevonden')

        return ver

    def _check_access(self, locatie, ver):
        if ver not in locatie.verenigingen.all():
            raise Http404('Locatie hoort niet bij de vereniging')

        _, functie_nu = rol_get_huidige_functie(self.request)

        # controleer dat de gebruiker HWL is van deze vereniging
        readonly = True
        if functie_nu and functie_nu.rol == 'HWL' and functie_nu.vereniging == ver:
            readonly = False

        return readonly

    def get(self, request, *args, **kwargs):
        context = dict()
        context['locatie'] = locatie = self.get_locatie()
        context['ver'] = ver = self.get_vereniging()
        context['readonly'] = readonly = self._check_access(locatie, ver)

        context['disc'] = disc = list()
        disc.append(('disc_outdoor', 'Outdoor', locatie.discipline_outdoor))
        disc.append(('disc_indoor', 'Indoor', locatie.discipline_indoor))
        disc.append(('disc_25m1p', '25m 1pijl', locatie.discipline_25m1pijl))
        disc.append(('disc_veld', 'Veld', locatie.discipline_veld))
        disc.append(('disc_3d', '3D', locatie.discipline_3d))
        disc.append(('disc_run', 'Run archery', locatie.discipline_run))
        disc.append(('disc_clout', 'Clout', locatie.discipline_clout))

        # aantal banen waar uit gekozen kan worden, voor gebruik in de template
        context['banen'] = [nr for nr in range(2, 24+1)]          # 1 baan = handmatig in .dtl

        # aantal banen waar uit gekozen kan worden, voor gebruik in de template
        context['buiten_banen'] = [nr for nr in range(2, 80+1)]   # 1 baan = handmatig in .dtl
        context['buiten_max_afstand'] = [nr for nr in range(30, 100+1, 10)]

        if not readonly:
            url = reverse('Locatie:extern-locatie-details',
                          kwargs={'ver_nr': ver.ver_nr,
                                  'locatie_pk': locatie.pk})
            context['url_opslaan'] = url
            context['url_verwijder'] = url

        context['url_terug'] = reverse('Locatie:externe-locaties',
                                       kwargs={'ver_nr': ver.ver_nr})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (reverse('Locatie:externe-locaties', kwargs={'ver_nr': ver.ver_nr}), 'Locaties'),
            (None, 'Locatie details')
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        locatie = self.get_locatie()
        ver = self.get_vereniging()
        readonly = self._check_access(locatie, ver)
        if readonly:
            raise PermissionDenied('Wijzigen alleen door HWL van de vereniging')

        door_account = get_account(request)

        if request.POST.get('verwijder', ''):
            locatie.zichtbaar = False
            locatie.save(update_fields=['zichtbaar'])

            # FUTURE: als de locatie nergens meer gebruikt wordt, dan kan deze opgeruimd worden

            url = reverse('Locatie:externe-locaties',
                          kwargs={'ver_nr': ver.ver_nr})
            return HttpResponseRedirect(url)

        data = request.POST.get('naam', '')
        if locatie.naam != data:
            activiteit = "Aanpassing naam externe locatie van vereniging %s: %s (was %s)" % (
                            ver, repr(data), repr(locatie.naam))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.naam = data

        data = request.POST.get('adres', '')
        data = data.replace('\r\n', '\n')
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

        data = request.POST.get('plaats', '')[:50]
        if locatie.plaats != data:
            activiteit = "Aanpassing plaats van externe locatie %s van vereniging %s: %s (was %s)" % (
                            locatie.naam, ver,
                            repr(data),
                            repr(locatie.plaats))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.plaats = data

        disc_old = locatie.disciplines_str()
        locatie.discipline_25m1pijl = (request.POST.get('disc_25m1p', '') != '')
        locatie.discipline_outdoor = (request.POST.get('disc_outdoor', '') != '')
        locatie.discipline_indoor = (request.POST.get('disc_indoor', '') != '')
        locatie.discipline_clout = (request.POST.get('disc_clout', '') != '')
        locatie.discipline_veld = (request.POST.get('disc_veld', '') != '')
        locatie.discipline_run = (request.POST.get('disc_run', '') != '')
        locatie.discipline_3d = (request.POST.get('disc_3d', '') != '')
        disc_new = locatie.disciplines_str()
        if disc_old != disc_new:
            activiteit = "Aanpassing disciplines van externe locatie %s van vereniging %s: [%s] (was [%s])" % (
                            locatie.naam, ver, disc_new, disc_old)
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)

        # extra velden voor indoor locaties
        if locatie.discipline_indoor or locatie.discipline_25m1pijl:
            try:
                banen = int(request.POST.get('banen_18m', 0))
                banen = max(banen, 0)   # ondergrens
                banen = min(banen, 24)  # bovengrens
            except ValueError:
                banen = 0
            if locatie.banen_18m != banen:
                activiteit = "Aanpassing aantal 18m banen van externe locatie %s" % locatie.naam
                activiteit += " van vereniging %s naar %s (was %s)" % (ver, banen, locatie.banen_18m)
                schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
                locatie.banen_18m = banen

            try:
                banen = int(request.POST.get('banen_25m', 0))
                banen = max(banen, 0)   # ondergrens
                banen = min(banen, 24)  # bovengrens
            except ValueError:
                banen = 0
            if locatie.banen_25m != banen:
                activiteit = "Aanpassing aantal 25m banen van externe locatie %s" % locatie.naam
                activiteit += " van vereniging %s naar %s (was %s)" % (ver, banen, locatie.banen_25m)
                schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
                locatie.banen_25m = banen

            try:
                sporters = int(request.POST.get('max_sporters_18m', 0))
                sporters = max(sporters, 0)     # ondergrens
                sporters = min(sporters, 99)    # bovengrens
            except ValueError:
                sporters = 0
            if locatie.max_sporters_18m != sporters:
                activiteit = "Aanpassing maximum sporters 18m van externe locatie %s" % locatie.naam
                activiteit += " van vereniging %s naar %s (was %s)" % (ver, sporters, locatie.max_sporters_18m)
                schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
                locatie.max_sporters_18m = sporters

            try:
                sporters = int(request.POST.get('max_sporters_25m', 0))
                sporters = max(sporters, 0)     # ondergrens
                sporters = min(sporters, 99)    # bovengrens
            except ValueError:
                sporters = 0
            if locatie.max_sporters_25m != sporters:
                activiteit = "Aanpassing maximum sporters 25m van externe locatie %s" % locatie.naam
                activiteit += " van vereniging %s naar %s (was %s)" % (ver, sporters, locatie.max_sporters_25m)
                schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
                locatie.max_sporters_25m = sporters

        # extra velden voor outdoor locaties
        if locatie.discipline_outdoor or locatie.discipline_veld:
            try:
                max_afstand = int(request.POST.get('buiten_max_afstand', 0))
                max_afstand = max(max_afstand, 30)    # ondergrens
                max_afstand = min(max_afstand, 100)   # bovengrens
            except ValueError:
                max_afstand = 30

            try:
                banen = int(request.POST.get('buiten_banen', 0))
                banen = max(banen, 1)   # ondergrens
                banen = min(banen, 80)  # bovengrens
            except ValueError:
                banen = 0

            if max_afstand != locatie.buiten_max_afstand or banen != locatie.buiten_banen:
                activiteit = "Aanpassing aantal outdoor banen van externe locatie %s" % locatie.naam
                activiteit += " van vereniging %s: naar %s x %s meter (was %s x %sm)" % (
                                ver,
                                banen, max_afstand,
                                locatie.buiten_banen, locatie.buiten_max_afstand)
                schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
                locatie.buiten_max_afstand = max_afstand
                locatie.buiten_banen = banen

        data = request.POST.get('notities', '')
        data = data.replace('\r\n', '\n')
        if locatie.notities != data:
            activiteit = "Aanpassing bijzonderheden van externe locatie %s" % locatie.naam
            activiteit += " van vereniging %s: %s (was %s)" % (
                            ver,
                            repr(data.replace('\n', ' / ')),
                            repr(locatie.notities.replace('\n', ' / ')))
            schrijf_in_logboek(door_account, 'Accommodaties', activiteit)
            locatie.notities = data

        locatie.save()

        url = reverse('Locatie:externe-locaties',
                      kwargs={'ver_nr': ver.ver_nr})
        return HttpResponseRedirect(url)


# end of file
