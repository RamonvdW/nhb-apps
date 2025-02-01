# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige_functie
from Locatie.definities import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN, BAANTYPE2STR
from Locatie.forms import AccommodatieDetailsForm
from Locatie.models import WedstrijdLocatie
from Logboek.models import schrijf_in_logboek
from Vereniging.models import Vereniging, Secretaris


TEMPLATE_ACCOMMODATIE_DETAILS = 'locatie/accommodatie-details.dtl'


class VerenigingAccommodatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van de accommodatie van een vereniging gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_ACCOMMODATIE_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.functie_nu and self.rol_nu in (Rol.ROL_HWL, Rol.ROL_WL, Rol.ROL_SEC)

    def _mag_wijzigen(self, ver):
        """ Controleer of de huidige rol de instellingen van de accommodatie mag wijzigen """
        if self.rol_nu in (Rol.ROL_HWL, Rol.ROL_SEC):
            # HWL mag van zijn eigen vereniging wijzigen
            if self.functie_nu.vereniging == ver:
                return True
        return False

    @staticmethod
    def _get_vereniging_locaties_or_404(**kwargs):
        try:
            ver_nr = int(kwargs['ver_nr'][:6])    # afkappen voor de veiligheid
            ver = Vereniging.objects.select_related('regio').get(ver_nr=ver_nr)
        except Vereniging.DoesNotExist:
            raise Http404('Geen valide vereniging')

        clusters = list()
        for cluster in ver.clusters.order_by('letter').all():
            clusters.append(str(cluster))
        # for
        if len(clusters) > 0:
            ver.sorted_cluster_names = clusters

        # zoek de locaties erbij
        binnen_locatie = None
        buiten_locatie = None
        externe_locaties = list()
        for loc in ver.wedstrijdlocatie_set.all():
            if loc.baan_type == BAAN_TYPE_EXTERN:
                if loc.zichtbaar:
                    externe_locaties.append(loc)
            elif loc.baan_type == BAAN_TYPE_BUITEN:
                # ook zichtbaar=False doorlaten!
                buiten_locatie = loc
            else:
                # BAAN_TYPE_BINNEN_VOLLEDIG_OVERDEKT, BAAN_TYPE_BINNEN_BUITEN of BAAN_TYPE_ONBEKEND
                if loc.zichtbaar:
                    binnen_locatie = loc
        # for

        return binnen_locatie, buiten_locatie, externe_locaties, ver

    @staticmethod
    def get_all_names(functie):
        return [account.volledige_naam() for account in functie.accounts.all()]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        binnen_locatie, buiten_locatie, externe_locaties, ver = self._get_vereniging_locaties_or_404(**kwargs)
        context['locatie'] = binnen_locatie
        if buiten_locatie and buiten_locatie.zichtbaar:
            context['buiten_locatie'] = buiten_locatie
        context['externe_locaties'] = externe_locaties
        context['ver'] = ver

        for locatie in externe_locaties:
            locatie.geen_naam = locatie.naam.strip() == ""
            locatie.geen_plaats = locatie.plaats.strip() == ""
            locatie.geen_disciplines = locatie.disciplines_str() == ""
        # for

        # zoek de beheerders erbij
        qset = Functie.objects.filter(vereniging=ver).prefetch_related('accounts')
        try:
            functie_sec = qset.filter(rol='SEC')[0]
        except IndexError:
            # only in autotest environment
            raise Http404('Rol ontbreekt')

        if ver.is_extern:
            functie_hwl = functie_wl = None
        else:
            try:
                functie_hwl = qset.filter(rol='HWL')[0]
                functie_wl = qset.filter(rol='WL')[0]
            except IndexError:
                # only in autotest environment
                raise Http404('Rol ontbreekt')

        context['sec_names'] = self.get_all_names(functie_sec)
        context['sec_email'] = functie_sec.bevestigde_email

        if len(context['sec_names']) == 0:
            context['geen_sec'] = True
            try:
                sec = Secretaris.objects.prefetch_related('sporters').get(vereniging=functie_sec.vereniging)
            except Secretaris.DoesNotExist:
                pass
            else:
                if sec.sporters.count() > 0:            # pragma: no branch
                    context['sec_names'] = [sporter.volledige_naam() for sporter in sec.sporters.all()]
                    context['geen_sec'] = False

        if functie_hwl:
            context['toon_hwl'] = True
            context['hwl_names'] = self.get_all_names(functie_hwl)
            context['hwl_email'] = functie_hwl.bevestigde_email
        else:
            context['toon_hwl'] = False

        if functie_wl:
            context['toon_wl'] = True
            context['wl_names'] = self.get_all_names(functie_wl)
            context['wl_email'] = functie_wl.bevestigde_email
        else:
            context['toon_wl'] = False

        if binnen_locatie:
            # beschrijving voor de template
            binnen_locatie.baan_type_str = BAANTYPE2STR[binnen_locatie.baan_type]

            # aantal banen waar uit gekozen kan worden, voor gebruik in de template
            context['banen'] = [nr for nr in range(2, 24+1)]          # 1 baan = handmatig in .dtl

            # lijst van verenigingen voor de template
            binnen_locatie.other_ver = binnen_locatie.verenigingen.exclude(ver_nr=ver.ver_nr).order_by('ver_nr')

        if buiten_locatie:
            # aantal banen waar uit gekozen kan worden, voor gebruik in de template
            context['buiten_banen'] = [nr for nr in range(2, 80+1)]   # 1 baan = handmatig in .dtl
            context['buiten_max_afstand'] = [nr for nr in range(30, 100+1, 10)]

            context['disc'] = disc = list()
            disc.append(('disc_outdoor', 'Outdoor', buiten_locatie.discipline_outdoor))
            # disc.append(('disc_indoor', 'Indoor', buiten_locatie.discipline_indoor))
            disc.append(('disc_25m1p', '25m 1pijl', buiten_locatie.discipline_25m1pijl))
            disc.append(('disc_veld', 'Veld', buiten_locatie.discipline_veld))
            disc.append(('disc_3d', '3D', buiten_locatie.discipline_3d))
            disc.append(('disc_run', 'Run archery', buiten_locatie.discipline_run))
            disc.append(('disc_clout', 'Clout', buiten_locatie.discipline_clout))

        # terug en opslaan knoppen voor in de template
        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer Vereniging'),
            (None, 'Accommodatie')
        )

        if self._mag_wijzigen(ver):
            context['readonly'] = False

            if binnen_locatie or buiten_locatie:
                context['opslaan_url'] = reverse('Locatie:accommodatie-details',
                                                 kwargs={'ver_nr': ver.ver_nr})

            if buiten_locatie and buiten_locatie.zichtbaar:
                context['url_verwijder_buitenbaan'] = context['opslaan_url']
        else:
            context['readonly'] = True

        return context

    @staticmethod
    def _wijzig_binnenbaan(form, ver, binnen_locatie, account):
        msgs = list()
        data = form.cleaned_data.get('baan_type')
        if data and binnen_locatie.baan_type != data:
            old_str = BAANTYPE2STR[binnen_locatie.baan_type]
            new_str = BAANTYPE2STR[data]
            msgs.append("baan type aangepast van '%s' naar '%s'" % (old_str, new_str))
            binnen_locatie.baan_type = data

        data = form.cleaned_data.get('banen_18m')
        if data and binnen_locatie.banen_18m != data:
            msgs.append("Aantal 18m banen aangepast van %s naar %s" % (binnen_locatie.banen_18m, data))
            binnen_locatie.banen_18m = data

        data = form.cleaned_data.get('banen_25m')
        if data and binnen_locatie.banen_25m != data:
            msgs.append("Aantal 25m banen aangepast van %s naar %s" % (binnen_locatie.banen_25m, data))
            binnen_locatie.banen_25m = data

        # data = form.cleaned_data.get('max_dt')
        # if binnen_locatie.max_dt_per_baan != data:
        #     msgs.append("Max DT per baan aangepast van %s naar %s" % (binnen_locatie.max_dt_per_baan, data))
        #     binnen_locatie.max_dt_per_baan = data

        data_18 = form.cleaned_data.get('max_sporters_18m')
        data_25 = form.cleaned_data.get('max_sporters_25m')
        if data_18 and data_25:
            if binnen_locatie.max_sporters_18m != data_18 or binnen_locatie.max_sporters_25m != data_25:
                msgs.append("Max sporters 18m/25m aangepast van %s/%s naar %s/%s" % (
                    binnen_locatie.max_sporters_18m, binnen_locatie.max_sporters_25m, data_18, data_25))
                binnen_locatie.max_sporters_18m = data_18
                binnen_locatie.max_sporters_25m = data_25

        if len(msgs) > 0:
            activiteit = "Aanpassingen aan binnen locatie van vereniging %s: %s" % (ver, "; ".join(msgs))
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
            binnen_locatie.save()

        disc_old = binnen_locatie.disciplines_str()
        binnen_locatie.discipline_indoor = (str(binnen_locatie.banen_18m) != "0" or
                                            str(binnen_locatie.banen_25m) != "0")
        binnen_locatie.discipline_25m1pijl = False
        binnen_locatie.discipline_outdoor = False
        binnen_locatie.discipline_clout = False
        binnen_locatie.discipline_veld = False
        binnen_locatie.discipline_run = False
        binnen_locatie.discipline_3d = False
        disc_new = binnen_locatie.disciplines_str()
        if disc_old != disc_new:
            activiteit = "Aanpassing disciplines van binnen locatie van vereniging %s: [%s] (was [%s])" % (
                ver, disc_new, disc_old)
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
            binnen_locatie.save()

        data = form.cleaned_data.get('notities')
        data = data.replace('\r\n', '\n')
        if binnen_locatie.notities != data:
            activiteit = "Aanpassing bijzonderheden van binnen locatie van vereniging %s: %s (was %s)" % (
                ver,
                repr(data.replace('\n', ' / ')),
                repr(binnen_locatie.notities.replace('\n', ' / ')))
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
            binnen_locatie.notities = data
            binnen_locatie.save()

    @staticmethod
    def _wijzig_buitenbaan(form, ver, buiten_locatie, account):
        msgs = list()
        do_save = False

        data = form.cleaned_data.get('buiten_banen')
        if data and buiten_locatie.buiten_banen != data:
            msgs.append("Aantal buiten banen aangepast van %s naar %s" % (buiten_locatie.buiten_banen, data))
            buiten_locatie.buiten_banen = data
            do_save = True

        data = form.cleaned_data.get('buiten_max_afstand')
        if data and buiten_locatie.buiten_max_afstand != data:
            msgs.append("Maximale afstand aangepast van %s naar %s" % (buiten_locatie.buiten_max_afstand, data))
            buiten_locatie.buiten_max_afstand = data
            do_save = False

        if len(msgs) > 0:
            activiteit = "Aanpassingen aan buiten locatie van vereniging %s: %s" % (ver, "; ".join(msgs))
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
        del msgs

        data = form.cleaned_data.get('buiten_notities')
        data = data.replace('\r\n', '\n')
        if buiten_locatie.notities != data:
            activiteit = "Aanpassing notitie van buiten locatie van vereniging %s: %s (was %s)" % (ver,
                            repr(data.replace('\n', ' / ')),
                            repr(buiten_locatie.notities.replace('\n', ' / ')))
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
            buiten_locatie.notities = data
            do_save = True

        disc_old = buiten_locatie.disciplines_str()
        buiten_locatie.discipline_25m1pijl = form.cleaned_data.get('disc_25m1p')
        buiten_locatie.discipline_outdoor = form.cleaned_data.get('disc_outdoor')
        buiten_locatie.discipline_indoor = False
        buiten_locatie.discipline_clout = form.cleaned_data.get('disc_clout')
        buiten_locatie.discipline_veld = form.cleaned_data.get('disc_veld')
        buiten_locatie.discipline_run = form.cleaned_data.get('disc_run')
        buiten_locatie.discipline_3d = form.cleaned_data.get('disc_3d')
        disc_new = buiten_locatie.disciplines_str()
        if disc_old != disc_new:
            activiteit = "Aanpassing disciplines van buiten locatie van vereniging %s: [%s] (was [%s])" % (
                            ver, disc_new, disc_old)
            schrijf_in_logboek(account, 'Accommodaties', activiteit)
            do_save = True

        if do_save:
            buiten_locatie.save()

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruik op de 'opslaan' knop drukt
            op het accommodatie-details formulier.
        """
        binnen_locatie, buiten_locatie, _, ver = self._get_vereniging_locaties_or_404(**kwargs)

        if not self._mag_wijzigen(ver):
            raise PermissionDenied('Wijzigen niet toegestaan')

        if request.POST.get('verwijder_buitenbaan', None):
            if buiten_locatie:
                buiten_locatie.zichtbaar = False
                buiten_locatie.save(update_fields=['zichtbaar'])
            url = reverse('Locatie:accommodatie-details', kwargs={'ver_nr': ver.ver_nr})
            return HttpResponseRedirect(url)

        if request.POST.get('maak_buiten_locatie', None):
            if buiten_locatie:
                if not buiten_locatie.zichtbaar:
                    buiten_locatie.zichtbaar = True
                    buiten_locatie.save(update_fields=['zichtbaar'])
            elif binnen_locatie:
                buiten = WedstrijdLocatie(
                                baan_type=BAAN_TYPE_BUITEN,
                                adres_uit_crm=False,
                                adres=binnen_locatie.adres,
                                plaats=binnen_locatie.plaats,
                                notities='')
                buiten.save()
                buiten.verenigingen.add(ver)

            url = reverse('Locatie:accommodatie-details', kwargs={'ver_nr': ver.ver_nr})
            return HttpResponseRedirect(url)

        form = AccommodatieDetailsForm(request.POST)
        if not form.is_valid():
            raise Http404('Geen valide invoer')

        account = get_account(request)

        if binnen_locatie:
            self._wijzig_binnenbaan(form, ver, binnen_locatie, account)

        if buiten_locatie:
            self._wijzig_buitenbaan(form, ver, buiten_locatie, account)

        url = reverse('Vereniging:overzicht')
        return HttpResponseRedirect(url)

# end of file
