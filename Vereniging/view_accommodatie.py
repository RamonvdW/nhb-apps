# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from Functie.models import Functie
from NhbStructuur.models import NhbCluster, NhbVereniging
from Wedstrijden.models import WedstrijdLocatie, BAANTYPE2STR
from Logboek.models import schrijf_in_logboek
from .forms import AccommodatieDetailsForm
import copy


TEMPLATE_LIJST_VERENIGINGEN = 'vereniging/lijst-verenigingen.dtl'
TEMPLATE_ACCOMMODATIE_DETAILS = 'vereniging/accommodatie-details.dtl'
TEMPLATE_WIJZIG_CLUSTERS = 'vereniging/wijzig-clusters.dtl'


class LijstVerenigingenView(UserPassesTestMixin, ListView):

    """ Via deze view worden kan een BKO, RKO of RCL
          de lijst van verenigingen zien, in zijn werkgebied
    """

    template_name = TEMPLATE_LIJST_VERENIGINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_SEC)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .filter(regio__rayon=functie_nu.nhb_rayon)
                    .prefetch_related('wedstrijdlocatie_set', 'clusters')
                    .order_by('regio__regio_nr', 'nhb_nr'))

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('wedstrijdlocatie_set', 'clusters')
                    .order_by('regio__regio_nr', 'nhb_nr'))

        if rol_nu == Rollen.ROL_IT:
            # landelijke lijst + telling aantal leden
            objs = (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('nhblid_set', 'wedstrijdlocatie_set', 'clusters')
                    .order_by('regio__regio_nr', 'nhb_nr'))

            for obj in objs:
                obj.aantal_leden = obj.nhblid_set.count()
            # for
            return objs

        # vul een kleine cache om vele database verzoeken te voorkomen
        hwl_functies = dict()  # [nhb_ver] = Functie()
        for functie in (Functie
                        .objects
                        .filter(rol='HWL')
                        .select_related('nhb_ver')
                        .prefetch_related('accounts')):
            hwl_functies[functie.nhb_ver.nhb_nr] = functie
        # for

        # toon de lijst van verenigingen in de regio
        if rol_nu == Rollen.ROL_RCL:
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            objs = (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set', 'clusters')
                    .order_by('nhb_nr'))
        else:
            # rol_nu == Rollen.ROL_HWL / ROL_SEC
            # het regionummer is verkrijgbaar via de vereniging
            objs = (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_ver.regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set', 'clusters')
                    .order_by('nhb_nr'))

        for obj in objs:
            try:
                functie_hwl = hwl_functies[obj.nhb_nr]
            except KeyError:
                # deze vereniging heeft geen HWL functie
                obj.hwls = list()
            else:
                obj.hwls = functie_hwl.accounts.all()
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['toon_rayon'] = True
        context['toon_regio'] = True
        context['toon_cluster'] = False
        context['toon_details'] = True
        context['toon_ledental'] = False
        menu_actief = 'hetplein'

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        context['landelijk'] = rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO)

        if rol_nu == Rollen.ROL_IT:
            context['toon_ledental'] = True

        if rol_nu == Rollen.ROL_RKO:
            context['toon_rayon'] = False

        if rol_nu in (Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_SEC):
            context['toon_rayon'] = False
            context['toon_regio'] = False
            if rol_nu == Rollen.ROL_HWL:
                menu_actief = 'vereniging'

        # voeg de url toe voor de "details" knoppen
        for nhbver in context['object_list']:
            for loc in nhbver.wedstrijdlocatie_set.all():
                loc.details_url = reverse('Vereniging:accommodatie-details', kwargs={'locatie_pk': loc.pk, 'vereniging_pk': nhbver.pk})
            # for
            if nhbver.clusters.count() > 0:
                context['toon_cluster'] = True
                letters = [cluster.letter for cluster in nhbver.clusters.all()]
                letters.sort()
                nhbver.cluster_letters = ",".join(letters)

                if not context['toon_regio']:
                    # verander in 101a,b
                    nhbver.cluster_letters = str(nhbver.regio.regio_nr) + nhbver.cluster_letters
        # for

        menu_dynamics(self.request, context, actief=menu_actief)
        return context


class AccommodatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een wedstrijdlocatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_ACCOMMODATIE_DETAILS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL, Rollen.ROL_SEC)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_locatie_nhver_or_404(**kwargs):
        try:
            locatie_pk = int(kwargs['locatie_pk'][:6])      # afkappen voor veiligheid
            locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except (ValueError, WedstrijdLocatie.DoesNotExist):
            raise Resolver404()

        try:
            nhbver_pk = int(kwargs['vereniging_pk'][:6])    # afkappen voor veiligheid
            nhbver = NhbVereniging.objects.get(pk=nhbver_pk)
        except NhbVereniging.DoesNotExist:
            raise Resolver404()

        # controleer dat de twee coherent zijn
        if locatie.verenigingen.filter(nhb_nr=nhbver.nhb_nr).count() == 0:
            # vereniging hoort niet bij deze locatie
            raise Resolver404()

        clusters = list()
        for cluster in nhbver.clusters.order_by('letter').all():
            clusters.append(str(cluster))
        # for
        if len(clusters) > 0:
            nhbver.sorted_cluster_names = clusters

        return locatie, nhbver

    def _mag_wijzigen(self, nhbver):
        """ Controleer of de huidige rol de instellingen van de accommodatie mag wijzigen """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

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

        locatie, nhbver = self._get_locatie_nhver_or_404(**kwargs)
        context['locatie'] = locatie
        context['nhbver'] = nhbver

        # zoek de beheerders erbij
        qset = Functie.objects.filter(nhb_ver=nhbver).prefetch_related('accounts')
        try:
            functie_sec = qset.filter(rol='SEC')[0]
            functie_hwl = qset.filter(rol='HWL')[0]
            functie_wl = qset.filter(rol='WL')[0]
        except IndexError:                  # pragma: no cover
            # only in autotest environment
            print("Vereniging.views.AccommodatieDetailsView: autotest ontbreekt rol SEC, HWL of WL")
            raise Resolver404()

        context['sec_names'] = self.get_all_names(functie_sec)
        context['sec_email'] = functie_sec.bevestigde_email

        if len(context['sec_names']) == 0 and nhbver.secretaris_lid:
            context['sec_names'] = [nhbver.secretaris_lid.volledige_naam(),]

        context['hwl_names'] = self.get_all_names(functie_hwl)
        context['hwl_email'] = functie_hwl.bevestigde_email

        context['wl_names'] = self.get_all_names(functie_wl)
        context['wl_email'] = functie_wl.bevestigde_email

        # beschrijving voor de template
        locatie.baan_type_str = BAANTYPE2STR[locatie.baan_type]

        # lijst van verenigingen voor de template
        locatie.other_ver = locatie.verenigingen.exclude(nhb_nr=nhbver.nhb_nr).order_by('nhb_nr')

        # terug en opslaan knoppen voor in de template
        if 'is_ver' in kwargs:
            context['terug_url'] = reverse('Vereniging:overzicht')
            opslaan_urlconf = 'Vereniging:vereniging-accommodatie-details'
            menu_actief = 'vereniging'
        else:
            context['terug_url'] = reverse('Vereniging:lijst-verenigingen')
            opslaan_urlconf = 'Vereniging:accommodatie-details'
            menu_actief = 'hetplein'

        if self._mag_wijzigen(nhbver):
            context['readonly'] = False
            context['opslaan_url'] = reverse(opslaan_urlconf, kwargs={'locatie_pk': locatie.pk,
                                                                      'vereniging_pk': nhbver.pk})

            rol_nu = rol_get_huidige(self.request)

            # geef ook meteen de mogelijkheid om leden te koppelen aan rollen
            if rol_nu == Rollen.ROL_SEC:
                context['url_koppel_sec'] = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie_sec.pk})
            context['url_koppel_hwl'] = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie_hwl.pk})
            context['url_koppel_wl'] = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie_wl.pk})

            # geef ook meteen de mogelijkheid om de e-mailadressen van een functie aan te passen
            context['url_email_hwl'] = reverse('Functie:wijzig-email', kwargs={'functie_pk': functie_hwl.pk})
            context['url_email_wl'] = reverse('Functie:wijzig-email', kwargs={'functie_pk': functie_wl.pk})
        else:
            context['readonly'] = True

        # aantal banen waar uit gekozen kan worden, voor gebruik in de template
        context['banen'] = [nr for nr in range(2, 25)]

        menu_dynamics(self.request, context, actief=menu_actief)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruik op de 'opslaan' knop drukt
            op het accommodatie-details formulier.
        """
        locatie, nhbver = self._get_locatie_nhver_or_404(**kwargs)

        form = AccommodatieDetailsForm(request.POST)
        if not form.is_valid():
            raise Resolver404()

        if not self._mag_wijzigen(nhbver):
            raise Resolver404()

        msgs = list()
        data = form.cleaned_data.get('baan_type')
        if locatie.baan_type != data:
            old_str = BAANTYPE2STR[locatie.baan_type]
            new_str = BAANTYPE2STR[data]
            msgs.append("baan type aangepast van '%s' naar '%s'" % (old_str, new_str))
            locatie.baan_type = data

        data = form.cleaned_data.get('banen_18m')
        if locatie.banen_18m != data:
            msgs.append("Aantal 18m banen aangepast van %s naar %s" % (locatie.banen_18m, data))
            locatie.banen_18m = data

        data = form.cleaned_data.get('banen_25m')
        if locatie.banen_25m != data:
            msgs.append("Aantal 25m banen aangepast van %s naar %s" % (locatie.banen_25m, data))
            locatie.banen_25m = data

        data = form.cleaned_data.get('max_dt')
        if locatie.max_dt_per_baan != data:
            msgs.append("Max DT per baan aangepast van %s naar %s" % (locatie.max_dt_per_baan, data))
            locatie.max_dt_per_baan = data

        if len(msgs) > 0:
            activiteit = "Aanpassingen aan locatie %s: %s" % (str(locatie), "; ".join(msgs))
            schrijf_in_logboek(request.user, 'Accommodaties', activiteit)

        data = form.cleaned_data.get('notities')
        if locatie.notities != data:
            activiteit = "Aanpassing notitie van locatie %s: %s (was %s)" % (str(locatie), repr(data), repr(locatie.notities))
            schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
            locatie.notities = data

        locatie.save()

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


class WijzigClustersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen verenigingen in de clusters geplaatst worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WIJZIG_CLUSTERS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pk2cluster = dict()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # filter clusters die aangepast mogen worden op competitie type
        # waarvan de definitie heel handig overeen komt met cluster.gebruik
        context['gebruik'] = gebruik_filter = functie_nu.comp_type

        # cluster namen
        objs = (NhbCluster
                .objects
                .filter(regio=functie_nu.nhb_regio, gebruik=gebruik_filter)
                .select_related('regio')
                .order_by('letter'))
        context['cluster_list'] = objs
        context['regio_heeft_clusters'] = objs.count() > 0

        for obj in objs:
            obj.veld_naam = "naam_%s" % obj.pk
        # for

        # maak lijstje voor het formulier met de keuze opties van de pull-down lijstjes
        opts = objs[:]
        for opt in opts:
            opt.tekst = opt.cluster_code_str()
            opt.choice_name = str(opt.pk)       # gebruik de cluster pk als selector
        # for

        # voeg de "geen cluster" opties toe
        opt_geen = NhbCluster()
        opt_geen.tekst = "Geen"
        opt_geen.choice_name = "0"
        opts.insert(0, opt_geen)

        # vereniging in de regio
        objs = (NhbVereniging
                .objects
                .filter(regio=functie_nu.nhb_regio)
                .prefetch_related('clusters')
                .order_by('nhb_nr'))
        context['object_list'] = objs

        for obj in objs:
            # voeg form-fields toe die voor de post gebruikt kunnen worden
            obj.veld_naam = 'ver_' + str(obj.nhb_nr)

            # maak een kopie om een vlag te kunnen zetten op de huidige optie
            obj.cluster_opties = copy.deepcopy(opts)

            # zet de 'selected' vlag op de huidige cluster keuzes voor de vereniging
            for cluster in obj.clusters.all():
                # zoek dit cluster op
                for opt in obj.cluster_opties:
                    if opt.pk == cluster.pk:
                        opt.actief = True
                # for
            # for
        # for

        context['terug_url'] = reverse('Plein:plein')

        context['handleiding_clusters_url'] = reverse('Handleiding:Clusters')

        menu_dynamics(self.request, context, actief='hetplein')
        return context

    def _swap_cluster(self, nhbver, gebruik):
        # vertaal de post value naar een NhbCluster object
        # checkt ook meteen dat het een valide cluster is voor deze regio

        param_name = 'ver_' + str(nhbver.nhb_nr)
        post_param = self.request.POST.get(param_name, None)

        cluster_pk = None
        if post_param is not None:
            try:
                cluster_pk = int(post_param)
            except (ValueError, TypeError):
                return

        if cluster_pk is not None:
            try:
                new_cluster = self._pk2cluster[cluster_pk]
            except KeyError:
                new_cluster = None

            try:
                huidige = nhbver.clusters.get(gebruik=gebruik)
            except NhbCluster.DoesNotExist:
                # vereniging zit niet in een cluster voor de 18m
                # stop de vereniging in het gevraagde cluster
                if new_cluster:
                    nhbver.clusters.add(new_cluster)
                    activiteit = "Vereniging %s toegevoegd aan cluster %s" % (nhbver, new_cluster)
                    schrijf_in_logboek(self.request.user, 'Clusters', activiteit)
                return

            # vereniging zit al in een cluster voor dit gebruik
            if huidige != new_cluster:
                # nieuwe keuze is anders, dus verwijder de vereniging uit dit cluster
                nhbver.clusters.remove(huidige)
                activiteit = "Vereniging %s verwijderd uit cluster %s" % (nhbver, huidige)
                schrijf_in_logboek(self.request.user, 'Clusters', activiteit)

                # stop de vereniging in het gevraagde cluster (if any)
                if new_cluster:
                    nhbver.clusters.add(new_cluster)
                    activiteit = "Vereniging %s toegevoegd aan cluster %s" % (nhbver, new_cluster)
                    schrijf_in_logboek(self.request.user, 'Clusters', activiteit)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de RCL op de 'opslaan' knop drukt
            in het wijzig-clusters formulier.
        """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # filter clusters die aangepast mogen worden op competitie type
        # waarvan de definitie heel handig overeen komt met cluster.gebruik
        gebruik_filter = functie_nu.comp_type

        clusters = (NhbCluster
                    .objects
                    .filter(regio=functie_nu.nhb_regio,
                            gebruik=gebruik_filter))

        # neem de cluster namen over
        for obj in clusters:
            self._pk2cluster[obj.pk] = obj

            # haal de ingevoerde naam van het cluster op
            cluster_veld = "naam_%s" % obj.pk
            naam = request.POST.get(cluster_veld, obj.naam)
            if naam != obj.naam:
                # wijziging opslaan
                obj.naam = naam[:50]        # te lang kan anders niet opgeslagen worden
                obj.save()
        # for

        # neem de cluster keuzes voor de verenigingen over
        for obj in (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_regio)
                    .prefetch_related('clusters')):

            self._swap_cluster(obj, gebruik_filter)
        # for

        url = reverse('Plein:plein')
        return HttpResponseRedirect(url)


# end of file
