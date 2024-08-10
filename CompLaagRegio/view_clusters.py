# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.models import Regiocompetitie
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige_functie, rol_get_beschrijving
from Geo.models import Cluster
from Logboek.models import schrijf_in_logboek
from Vereniging.models import Vereniging
import copy


TEMPLATE_COMPREGIO_WIJZIG_CLUSTERS = 'complaagregio/wijzig-clusters.dtl'


class WijzigClustersView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen verenigingen in de clusters geplaatst worden """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPREGIO_WIJZIG_CLUSTERS
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pk2cluster = dict()
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rollen.ROL_RCL

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # filter clusters die aangepast mogen worden op competitie type
        # waarvan de definitie heel handig overeen komt met cluster.gebruik
        context['gebruik'] = gebruik_filter = self.functie_nu.comp_type

        # cluster namen
        objs = (Cluster
                .objects
                .filter(regio=self.functie_nu.regio, gebruik=gebruik_filter)
                .select_related('regio')
                .order_by('letter'))
        context['cluster_list'] = objs
        context['regio_heeft_clusters'] = objs.count() > 0
        context['opslaan_url'] = reverse('CompLaagRegio:clusters')

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
        opt_geen = Cluster()
        opt_geen.tekst = "Geen"
        opt_geen.choice_name = "0"
        opts.insert(0, opt_geen)

        # vereniging in de regio
        objs = (Vereniging
                .objects
                .filter(regio=self.functie_nu.regio)
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

        context['email_support'] = settings.EMAIL_SUPPORT

        try:
            regiocompetitie = (Regiocompetitie
                               .objects
                               .filter(regio=self.functie_nu.regio,
                                       competitie__afstand=self.functie_nu.comp_type)
                               .order_by('-competitie__begin_jaar')     # hoogste (nieuwste) eerst
                               .first())
        except Regiocompetitie.DoesNotExist:
            # geen competitie gevonden, dus ga naar de keuze pagina
            context['kruimels'] = (
                (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                (None, 'Clusters')
            )
        else:
            # link terug naar de specifieke competitie
            if regiocompetitie:
                comp = regiocompetitie.competitie
                context['kruimels'] = (
                    (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                    (reverse('Competitie:overzicht', kwargs={'comp_pk_of_seizoen': comp.maak_seizoen_url()}),
                        comp.beschrijving.replace('competitie ', '')),
                    (None, 'Clusters')
                )
            else:
                # geen competitie gevonden, dus ga naar de keuze pagina
                context['kruimels'] = (
                    (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
                    (None, 'Clusters')
                )

        return context

    def _update_vereniging_clusters(self, ver, gebruik):
        # vertaal de post value naar een Cluster object
        # checkt ook meteen dat het een valide cluster is voor deze regio

        param_name = 'ver_' + str(ver.ver_nr)
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

            door_account = get_account(self.request)

            try:
                huidige = ver.clusters.get(gebruik=gebruik)
            except Cluster.DoesNotExist:
                # vereniging zit niet in een cluster voor dit gebruik (type competitie)
                # stop de vereniging in het gevraagde cluster
                if new_cluster:
                    ver.clusters.add(new_cluster)
                    activiteit = "Vereniging %s toegevoegd aan cluster %s" % (ver, new_cluster)
                    schrijf_in_logboek(door_account, 'Clusters', activiteit)
                return

            # vereniging zit al in een cluster voor dit gebruik
            if huidige != new_cluster:
                # nieuwe keuze is anders, dus verwijder de vereniging uit dit cluster
                ver.clusters.remove(huidige)
                activiteit = "Vereniging %s verwijderd uit cluster %s" % (ver, huidige)
                schrijf_in_logboek(door_account, 'Clusters', activiteit)

                # stop de vereniging in het gevraagde cluster (if any)
                if new_cluster:
                    ver.clusters.add(new_cluster)
                    activiteit = "Vereniging %s toegevoegd aan cluster %s" % (ver, new_cluster)
                    schrijf_in_logboek(door_account, 'Clusters', activiteit)

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de RCL op de 'opslaan' knop drukt
            in het wijzig-clusters formulier.
        """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # filter clusters die aangepast mogen worden op competitie type
        # waarvan de definitie heel handig overeenkomt met cluster.gebruik
        gebruik_filter = functie_nu.comp_type

        clusters = (Cluster
                    .objects
                    .filter(regio=functie_nu.regio,
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
        for obj in (Vereniging
                    .objects
                    .filter(regio=functie_nu.regio)
                    .prefetch_related('clusters')):

            self._update_vereniging_clusters(obj, gebruik_filter)
        # for

        # indien geen competitie gevonden, ga dan naar de keuze pagina
        url = reverse('Competitie:kies')

        try:
            regiocompetitie = (Regiocompetitie
                               .objects
                               .filter(regio=self.functie_nu.regio,
                                       competitie__afstand=self.functie_nu.comp_type)
                               .order_by('-competitie__begin_jaar')     # hoogste (nieuwste) eerst
                               .first())
        except Regiocompetitie.DoesNotExist:
            pass
        else:
            # link terug naar de specifieke competitie
            if regiocompetitie:
                url = reverse('Competitie:overzicht',
                              kwargs={'comp_pk_of_seizoen': regiocompetitie.competitie.maak_seizoen_url()})

        return HttpResponseRedirect(url)


# end of file
