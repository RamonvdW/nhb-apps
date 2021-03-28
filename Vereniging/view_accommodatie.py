# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.db.models import Count
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
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


class LijstVerenigingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view worden kan een BKO, RKO of RCL
          de lijst van verenigingen zien, in zijn werkgebied
    """

    template_name = TEMPLATE_LIJST_VERENIGINGEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_SEC)

    @staticmethod
    def _get_verenigingen(rol_nu, functie_nu):

        # vul een kleine cache om vele database verzoeken te voorkomen
        hwl_functies = dict()   # [nhb_ver] = Functie()
        functie2count = dict()  # [functie.pk] = aantal
        for functie in (Functie
                        .objects
                        .select_related('nhb_ver')
                        .annotate(accounts_count=Count('accounts'))
                        .all()):
            if functie.rol == 'HWL':
                hwl_functies[functie.nhb_ver.ver_nr] = functie

            functie2count[functie.pk] = functie.accounts_count
        # for

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .filter(regio__rayon=functie_nu.nhb_rayon)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr', 'ver_nr'))

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('regio__regio_nr', 'ver_nr'))

        if rol_nu == Rollen.ROL_IT:
            # landelijke lijst + telling aantal leden
            objs = (NhbVereniging
                    .objects
                    .select_related('regio', 'regio__rayon')
                    .exclude(regio__regio_nr=100)
                    .prefetch_related('wedstrijdlocatie_set',
                                      'functie_set',
                                      'clusters')
                    .annotate(nhblid_set_count=Count('nhblid'))
                    .order_by('regio__regio_nr', 'ver_nr'))

            for obj in objs:
                obj.aantal_leden = obj.nhblid_set_count
                obj.aantal_beheerders = 0
                for functie in obj.functie_set.all():
                    obj.aantal_beheerders += functie2count[functie.pk]
                # for
            # for
            return objs

        # toon de lijst van verenigingen in de regio
        if rol_nu == Rollen.ROL_RCL:
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            objs = (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))
        else:
            # rol_nu == Rollen.ROL_HWL / ROL_SEC
            # het regionummer is verkrijgbaar via de vereniging
            objs = (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_ver.regio)
                    .select_related('regio')
                    .prefetch_related('wedstrijdlocatie_set',
                                      'clusters')
                    .order_by('ver_nr'))

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

        context['verenigingen'] = verenigingen = self._get_verenigingen(rol_nu, functie_nu)

        # voeg de url toe voor de "details" knoppen
        for nhbver in verenigingen:

            nhbver.details_url = reverse('Vereniging:accommodatie-details',
                                         kwargs={'vereniging_pk': nhbver.pk})

            for loc in nhbver.wedstrijdlocatie_set.all():
                if loc.baan_type == 'B':
                    nhbver.buiten_locatie = loc
                else:
                    nhbver.locatie = loc
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
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL, Rollen.ROL_WL, Rollen.ROL_SEC)

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
        for loc in nhbver.wedstrijdlocatie_set.all():
            if loc.baan_type == 'B':
                buiten_locatie = loc
            else:
                binnen_locatie = loc
        # for

        return binnen_locatie, buiten_locatie, nhbver

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

        binnen_locatie, buiten_locatie, nhbver = self._get_locaties_nhbver_or_404(**kwargs)
        context['locatie'] = binnen_locatie
        context['buiten_locatie'] = buiten_locatie
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
            raise Http404()

        context['sec_names'] = self.get_all_names(functie_sec)
        context['sec_email'] = functie_sec.bevestigde_email

        if len(context['sec_names']) == 0 and nhbver.secretaris_lid:
            context['sec_names'] = [nhbver.secretaris_lid.volledige_naam()]

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
        binnen_locatie, buiten_locatie, nhbver = self._get_locaties_nhbver_or_404(**kwargs)

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if not self._mag_wijzigen(nhbver, rol_nu, functie_nu):
            raise PermissionDenied('Wijzigen niet toegestaan')

        if request.POST.get('maak_buiten_locatie', None):
            if buiten_locatie:
                # er is al een buitenlocatie
                raise Http404('Er is al een buitenlocatie')

            buiten = WedstrijdLocatie(
                            baan_type='B',
                            adres_uit_crm=False,
                            adres='',
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

            data = form.cleaned_data.get('max_dt')
            if binnen_locatie.max_dt_per_baan != data:
                msgs.append("Max DT per baan aangepast van %s naar %s" % (binnen_locatie.max_dt_per_baan, data))
                binnen_locatie.max_dt_per_baan = data

            if len(msgs) > 0:
                activiteit = "Aanpassingen aan locatie %s: %s" % (str(binnen_locatie), "; ".join(msgs))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                binnen_locatie.save()

            data = form.cleaned_data.get('notities')
            if binnen_locatie.notities != data:
                activiteit = "Aanpassing notitie van locatie %s: %s (was %s)" % (str(binnen_locatie), repr(data), repr(binnen_locatie.notities))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                binnen_locatie.notities = data
                binnen_locatie.save()

        if buiten_locatie:
            msgs = list()

            data = form.cleaned_data.get('buiten_banen')
            if buiten_locatie.buiten_banen != data:
                msgs.append("Aantal banen aangepast van %s naar %s" % (buiten_locatie.buiten_banen, data))
                buiten_locatie.buiten_banen = data

            data = form.cleaned_data.get('buiten_max_afstand')
            if buiten_locatie.buiten_max_afstand != data:
                msgs.append("Maximale afstand aangepast van %s naar %s" % (buiten_locatie.buiten_max_afstand, data))
                buiten_locatie.buiten_max_afstand = data

            if len(msgs) > 0:
                activiteit = "Aanpassingen aan buiten locatie %s: %s" % (str(buiten_locatie), "; ".join(msgs))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                buiten_locatie.save()

            data = form.cleaned_data.get('buiten_adres')
            if buiten_locatie.adres != data:
                activiteit = "Aanpassing adres van buiten locatie %s: %s (was %s)" % (str(buiten_locatie), repr(data), repr(buiten_locatie.adres))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                buiten_locatie.adres = data
                buiten_locatie.save()

            data = form.cleaned_data.get('buiten_notities')
            if buiten_locatie.notities != data:
                activiteit = "Aanpassing notitie van buiten locatie %s: %s (was %s)" % (str(buiten_locatie), repr(data), repr(buiten_locatie.notities))
                schrijf_in_logboek(request.user, 'Accommodaties', activiteit)
                buiten_locatie.notities = data
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


class WijzigClustersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen verenigingen in de clusters geplaatst worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WIJZIG_CLUSTERS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pk2cluster = dict()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu == Rollen.ROL_RCL

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
        context['opslaan_url'] = reverse('Vereniging:clusters')

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
                .order_by('ver_nr'))
        context['object_list'] = objs

        for obj in objs:
            # voeg form-fields toe die voor de post gebruikt kunnen worden
            obj.veld_naam = 'ver_' + str(obj.ver_nr)

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
        context['email_bondsburo'] = settings.EMAIL_BONDSBURO

        menu_dynamics(self.request, context, actief='hetplein')
        return context

    def _swap_cluster(self, nhbver, gebruik):
        # vertaal de post value naar een NhbCluster object
        # checkt ook meteen dat het een valide cluster is voor deze regio

        param_name = 'ver_' + str(nhbver.ver_nr)
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
