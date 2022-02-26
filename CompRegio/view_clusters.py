# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from NhbStructuur.models import NhbCluster, NhbVereniging
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
import copy


TEMPLATE_COMPREGIO_WIJZIG_CLUSTERS = 'compregio/wijzig-clusters.dtl'


class WijzigClustersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen verenigingen in de clusters geplaatst worden """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_WIJZIG_CLUSTERS
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

        context['terug_url'] = reverse('Competitie:kies')

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
        context['opslaan_url'] = reverse('CompRegio:clusters')

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

        context['handleiding_clusters_url'] = reverse('Handleiding:Clusters')
        context['email_bondsbureau'] = settings.EMAIL_BONDSBUREAU

        context['kruimels'] = (
            (reverse('Competitie:kies'), 'Bondscompetities'),
            (None, 'Clusters')
        )

        menu_dynamics(self.request, context)
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
                obj.save(update_fields=['naam'])
        # for

        # neem de cluster keuzes voor de verenigingen over
        for obj in (NhbVereniging
                    .objects
                    .filter(regio=functie_nu.nhb_regio)
                    .prefetch_related('clusters')):

            self._swap_cluster(obj, gebruik_filter)
        # for

        url = reverse('Competitie:kies')

        return HttpResponseRedirect(url)


# end of file
