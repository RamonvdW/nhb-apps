# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Functie.models import Functie
from NhbStructuur.models import NhbVereniging
from Plein.menu import menu_dynamics
from Sporter.models import Secretaris
from Wedstrijden.models import WedstrijdLocatie, BAANTYPE2STR
from Logboek.models import schrijf_in_logboek
from .forms import AccommodatieDetailsForm


TEMPLATE_ACCOMMODATIE_DETAILS = 'vereniging/accommodatie-details.dtl'


class AccommodatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een wedstrijdlocatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_ACCOMMODATIE_DETAILS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL, Rollen.ROL_SEC)

    @staticmethod
    def _get_locaties_nhbver_or_404(**kwargs):
        try:
            nhbver_pk = int(kwargs['vereniging_pk'][:6])    # afkappen voor veiligheid
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Http404('Geen valide vereniging')

        clusters = list()
        for cluster in nhbver.clusters.order_by('letter').all():
            clusters.append(str(cluster))
        # for
        if len(clusters) > 0:
            nhbver.sorted_cluster_names = clusters

        # zoek de locaties erbij
        binnen_locatie = None
        buiten_locatie = None
        externe_locaties = list()
        for loc in nhbver.wedstrijdlocatie_set.exclude(zichtbaar=False).all():
            if loc.baan_type == 'E':
                externe_locaties.append(loc)
            elif loc.baan_type == 'B':
                buiten_locatie = loc
            else:
                binnen_locatie = loc
        # for

        return binnen_locatie, buiten_locatie, externe_locaties, nhbver

    @staticmethod
    def _mag_wijzigen(nhbver, rol_nu, functie_nu):
        """ Controleer of de huidige rol de instellingen van de accommodatie mag wijzigen """
        if functie_nu:
            if rol_nu in (Rollen.ROL_HWL, Rollen.ROL_SEC):
                # HWL mag van zijn eigen vereniging wijzigen
                if functie_nu.nhb_ver == nhbver:
                    return True
            elif rol_nu == Rollen.ROL_RCL:
                # RCL mag van alle verenigingen in zijn regio de accommodatie instellingen wijzigen
                if functie_nu.nhb_regio == nhbver.regio:
                    return True

        return False

    @staticmethod
    def get_all_names(functie):
        return [account.volledige_naam() for account in functie.accounts.all()]

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        binnen_locatie, buiten_locatie, externe_locaties, nhbver = self._get_locaties_nhbver_or_404(**kwargs)
        if buiten_locatie and not buiten_locatie.zichtbaar:
            buiten_locatie = None
        context['locatie'] = binnen_locatie
        context['buiten_locatie'] = buiten_locatie
        context['externe_locaties'] = externe_locaties
        context['nhbver'] = nhbver

        for locatie in externe_locaties:
            locatie.geen_naam = locatie.naam.strip() == ""
            locatie.geen_plaats = locatie.plaats.strip() == ""
            locatie.geen_disciplines = locatie.disciplines_str() == ""
        # for

        # zoek de beheerders erbij
        qset = Functie.objects.filter(nhb_ver=nhbver).prefetch_related('accounts')
        try:
            functie_sec = qset.filter(rol='SEC')[0]
            functie_hwl = qset.filter(rol='HWL')[0]
            functie_wl = qset.filter(rol='WL')[0]
        except IndexError:                  # pragma: no cover
            # only in autotest environment
            print("Vereniging.views.AccommodatieDetailsView: autotest ontbreekt rol SEC, HWL of WL")
            raise Http404()

        context['sec_names'] = self.get_all_names(functie_sec)
        context['sec_email'] = functie_sec.bevestigde_email

        if len(context['sec_names']) == 0:
            context['geen_sec'] = True
            try:
                sec = Secretaris.objects.select_related('sporter').get(vereniging=functie_sec.nhb_ver)
            except Secretaris.DoesNotExist:
                pass
            else:
                if sec.sporter:
                    context['sec_names'] = [sec.sporter.volledige_naam()]
                    context['geen_sec'] = False

        print('geen_sec: %s' % context['geen_sec'])

        context['hwl_names'] = self.get_all_names(functie_hwl)
        context['hwl_email'] = functie_hwl.bevestigde_email

        context['wl_names'] = self.get_all_names(functie_wl)
        context['wl_email'] = functie_wl.bevestigde_email

        if binnen_locatie:
            # beschrijving voor de template
            binnen_locatie.baan_type_str = BAANTYPE2STR[binnen_locatie.baan_type]

            # aantal banen waar uit gekozen kan worden, voor gebruik in de template
            context['banen'] = [nr for nr in range(2, 24+1)]          # 1 baan = handmatig in .dtl

            # lijst van verenigingen voor de template
            binnen_locatie.other_ver = binnen_locatie.verenigingen.exclude(ver_nr=nhbver.ver_nr).order_by('ver_nr')

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
        if 'is_ver' in kwargs:      # wordt gezet door VerenigingAccommodatieDetailsView
            context['terug_url'] = reverse('Vereniging:overzicht')
            opslaan_urlconf = 'Vereniging:vereniging-accommodatie-details'
            menu_actief = 'vereniging'
        else:
            context['terug_url'] = reverse('Vereniging:lijst-verenigingen')
            opslaan_urlconf = 'Vereniging:accommodatie-details'
            menu_actief = 'hetplein'

        if binnen_locatie or buiten_locatie:
            context['opslaan_url'] = reverse(opslaan_urlconf,
                                             kwargs={'vereniging_pk': nhbver.pk})

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if self._mag_wijzigen(nhbver, rol_nu, functie_nu):
            context['readonly'] = False

            # geef ook meteen de mogelijkheid om leden te koppelen aan rollen
            if rol_nu == Rollen.ROL_SEC:
                context['url_koppel_sec'] = reverse('Functie:wijzig-beheerders',
                                                    kwargs={'functie_pk': functie_sec.pk})
            context['url_koppel_hwl'] = reverse('Functie:wijzig-beheerders',
                                                kwargs={'functie_pk': functie_hwl.pk})
            context['url_koppel_wl'] = reverse('Functie:wijzig-beheerders',
                                               kwargs={'functie_pk': functie_wl.pk})

            # geef ook meteen de mogelijkheid om de e-mailadressen van een functie aan te passen
            context['url_email_hwl'] = reverse('Functie:wijzig-email',
                                               kwargs={'functie_pk': functie_hwl.pk})
            context['url_email_wl'] = reverse('Functie:wijzig-email',
                                              kwargs={'functie_pk': functie_wl.pk})

            if buiten_locatie:
                context['url_verwijder_buitenbaan'] = context['opslaan_url']
        else:
            context['readonly'] = True

            if binnen_locatie:      # pragma: no branch
                if binnen_locatie.banen_18m + binnen_locatie.banen_25m > 0:
                    context['readonly_show_max_dt'] = True

        menu_dynamics(self.request, context, actief=menu_actief)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruik op de 'opslaan' knop drukt
            op het accommodatie-details formulier.
        """
        binnen_locatie, buiten_locatie, _, nhbver = self._get_locaties_nhbver_or_404(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if not self._mag_wijzigen(nhbver, rol_nu, functie_nu):
            raise PermissionDenied('Wijzigen niet toegestaan')

        if request.POST.get('verwijder_buitenbaan', None):
            if buiten_locatie:
                buiten_locatie.zichtbaar = False
                buiten_locatie.save()
            if 'is_ver' in kwargs:  # wordt gezet door VerenigingAccommodatieDetailsView
                urlconf = 'Vereniging:vereniging-accommodatie-details'
            else:
                urlconf = 'Vereniging:accommodatie-details'
            url = reverse(urlconf, kwargs={'vereniging_pk': nhbver.pk})
            return HttpResponseRedirect(url)

        if request.POST.get('maak_buiten_locatie', None):
            if buiten_locatie:
                if not buiten_locatie.zichtbaar:
                    buiten_locatie.zichtbaar = True
                    buiten_locatie.save()
            elif binnen_locatie:
                buiten = WedstrijdLocatie(
                                baan_type='B',
                                adres_uit_crm=False,
                                adres=binnen_locatie.adres,
                                plaats=binnen_locatie.plaats,
                                notities='')
                buiten.save()
                buiten.verenigingen.add(nhbver)

            if 'is_ver' in kwargs:  # wordt gezet door VerenigingAccommodatieDetailsView
                urlconf = 'Vereniging:vereniging-accommodatie-details'
            else:
                urlconf = 'Vereniging:accommodatie-details'
            url = reverse(urlconf, kwargs={'vereniging_pk': nhbver.pk})
            return HttpResponseRedirect(url)

        form = AccommodatieDetailsForm(request.POST)
        if not form.is_valid():
            raise Http404('Geen valide invoer')

        if binnen_locatie:
            msgs = list()
            data = form.cleaned_data.get('baan_type')
            if binnen_locatie.baan_type != data:
                old_str = BAANTYPE2STR[binnen_locatie.baan_type]
                new_str = BAANTYPE2STR[data]
                msgs.append("baan type aangepast van '%s' naar '%s'" % (old_str, new_str))
                binnen_locatie.baan_type = data

            data = form.cleaned_data.get('banen_18m')
            if binnen_locatie.banen_18m != data:
                msgs.append("Aantal 18m banen aangepast van %s naar %s" % (binnen_locatie.banen_18m, data))
                binnen_locatie.banen_18m = data

            data = form.cleaned_data.get('banen_25m')
            if binnen_locatie.banen_25m != data:
                msgs.append("Aantal 25m banen aangepast van %s naar %s" % (binnen_locatie.banen_25m, data))
                binnen_locatie.banen_25m = data

            # data = form.cleaned_data.get('max_dt')
            # if binnen_locatie.max_dt_per_baan != data:
            #     msgs.append("Max DT per baan aangepast van %s naar %s" % (binnen_locatie.max_dt_per_baan, data))
            #     binnen_locatie.max_dt_per_baan = data

            data_18 = form.cleaned_data.get('max_sporters_18m')
            data_25 = form.cleaned_data.get('max_sporters_25m')
            if data_18 is not None and data_25 is not None:
                if binnen_locatie.max_sporters_18m != data_18 or binnen_locatie.max_sporters_25m != data_25:
                    msgs.append("Max sporters 18m/25m aangepast van %s/%s naar %s/%s" % (binnen_locatie.max_sporters_18m, binnen_locatie.max_sporters_25m, data_18, data_25))
                    binnen_locatie.max_sporters_18m = data_18
                    binnen_locatie.max_sporters_25m = data_25

            if len(msgs) > 0:
                activiteit = "Aanpassingen aan binnen locatie van vereniging %s: %s" % (nhbver, "; ".join(msgs))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
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
                                nhbver, disc_new, disc_old)
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                binnen_locatie.save()

            data = form.cleaned_data.get('notities')
            data = data.replace('\r\n', '\n')
            if binnen_locatie.notities != data:
                activiteit = "Aanpassing bijzonderheden van binnen locatie van vereniging %s: %s (was %s)" % (
                                nhbver,
                                repr(data.replace('\n', ' / ')),
                                repr(binnen_locatie.notities.replace('\n', ' / ')))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                binnen_locatie.notities = data
                binnen_locatie.save()

        if buiten_locatie:
            msgs = list()
            updated = list()

            data = form.cleaned_data.get('buiten_banen')
            if buiten_locatie.buiten_banen != data:
                msgs.append("Aantal buiten banen aangepast van %s naar %s" % (buiten_locatie.buiten_banen, data))
                buiten_locatie.buiten_banen = data
                updated.append('buiten_banen')

            data = form.cleaned_data.get('buiten_max_afstand')
            if buiten_locatie.buiten_max_afstand != data:
                msgs.append("Maximale afstand aangepast van %s naar %s" % (buiten_locatie.buiten_max_afstand, data))
                buiten_locatie.buiten_max_afstand = data
                updated.append('buiten_max_afstand')

            if len(msgs) > 0:
                activiteit = "Aanpassingen aan buiten locatie van vereniging %s: %s" % (nhbver, "; ".join(msgs))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)

            buiten_locatie.save(update_fields=updated)

            data = form.cleaned_data.get('buiten_notities')
            data = data.replace('\r\n', '\n')
            if buiten_locatie.notities != data:
                activiteit = "Aanpassing notitie van buiten locatie van vereniging %s: %s (was %s)" % (
                                    nhbver,
                                    repr(data.replace('\n', ' / ')),
                                    repr(buiten_locatie.notities.replace('\n', ' / ')))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                buiten_locatie.notities = data
                buiten_locatie.save(update_fields=['notities'])

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
                                nhbver, disc_new, disc_old)
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                buiten_locatie.save()

        if 'is_ver' in kwargs:
            url = reverse('Vereniging:overzicht')
        else:
            url = reverse('Vereniging:lijst-verenigingen')

        return HttpResponseRedirect(url)


class VerenigingAccommodatieDetailsView(AccommodatieDetailsView):
    """ uitbreiding op AccommodatieDetailsView voor gebruik vanuit de vereniging
        overzicht pagina voor de SEC/HWL. De vlag 'is_ver' resulteer in andere "terug" urls.
    """
    def get_context_data(self, **kwargs):
        kwargs['is_ver'] = True
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        kwargs['is_ver'] = True
        return super().post(request, *args, **kwargs)


# end of file
