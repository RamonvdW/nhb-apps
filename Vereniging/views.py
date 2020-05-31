# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.utils import timezone
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from Functie.models import Functie
from BasisTypen.models import LeeftijdsKlasse, MAXIMALE_LEEFTIJD_JEUGD
from NhbStructuur.models import NhbLid, NhbVereniging
from Schutter.models import SchutterBoog
from Competitie.models import Competitie, AG_NUL, RegioCompetitieSchutterBoog, regiocompetitie_schutterboog_aanmelden
from Score.models import Score
from Wedstrijden.models import WedstrijdLocatie, BAANTYPE2STR
from Logboek.models import schrijf_in_logboek
from .forms import AccommodatieDetailsForm
import copy


TEMPLATE_OVERZICHT = 'vereniging/overzicht.dtl'
TEMPLATE_LEDENLIJST = 'vereniging/ledenlijst.dtl'
TEMPLATE_LEDEN_VOORKEUREN = 'vereniging/leden-voorkeuren.dtl'
TEMPLATE_LEDEN_AANMELDEN = 'vereniging/leden-aanmelden.dtl'
TEMPLATE_LIJST_VERENIGINGEN = 'vereniging/lijst-verenigingen.dtl'
TEMPLATE_ACCOMMODATIE_DETAILS = 'vereniging/accommodatie-details.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Deze view is voor de beheerders van de vereniging """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and rol_nu == Rollen.ROL_CWZ

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        if functie_nu.nhb_ver.wedstrijdlocatie_set.count() > 0:
            locatie = functie_nu.nhb_ver.wedstrijdlocatie_set.all()[0]
            context['accommodatie_details_url'] = reverse('Vereniging:vereniging-accommodatie-details', kwargs={'locatie_pk': locatie.pk})

        context['competities'] = Competitie.objects.filter(is_afgesloten=False)

        for comp in context['competities']:
            if comp.afstand == '18':
                comp.icon = static('plein/badge_nhb_indoor.png')
            else:
                comp.icon = static('plein/badge_nhb_25m1p.png')
        # for

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class LedenLijstView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDENLIJST

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        huidige_jaar = timezone.now().year  # TODO: check for correctness in last hours of the year (due to timezone)
        jeugdgrens = huidige_jaar - MAXIMALE_LEEFTIJD_JEUGD
        self._huidige_jaar = huidige_jaar

        _, functie_nu = rol_get_huidige_functie(self.request)
        qset = NhbLid.objects.filter(bij_vereniging=functie_nu.nhb_ver)

        objs = list()

        prev_lkl = None
        prev_wedstrijdleeftijd = 0

        # sorteer op geboorte jaar en daarna naam
        for obj in NhbLid.objects.\
                filter(bij_vereniging=functie_nu.nhb_ver).\
                filter(geboorte_datum__year__gte=jeugdgrens).\
                order_by('-geboorte_datum__year', 'achternaam', 'voornaam'):

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = huidige_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                                max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                                geslacht='M').order_by('max_wedstrijdleeftijd')[0]
                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            objs.append(obj)
        # for

        # volwassenen
        # sorteer op naam
        for obj in NhbLid.objects.\
                        filter(bij_vereniging=functie_nu.nhb_ver).\
                        filter(geboorte_datum__year__lt=jeugdgrens).\
                        order_by('achternaam', 'voornaam'):
            obj.leeftijdsklasse = None

            if not obj.is_actief_lid:
                obj.leeftijd = huidige_jaar - obj.geboorte_datum.year

            objs.append(obj)
        # for

        # zoek de laatste-inlog bij elk lid
        for nhblid in objs:
            nhblid.wijzig_url = reverse('Schutter:voorkeuren-nhblid', kwargs={'nhblid_pk': nhblid.pk})

            if nhblid.account:
                nhblid.laatste_inlog = nhblid.account.last_login
            else:
                nhblid.geen_inlog = 1
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        inactief = list()
        for obj in context['object_list']:
            if not obj.is_actief_lid:
                inactief.append(obj)
            elif obj.leeftijdsklasse:
                jeugd.append(obj)
            else:
                senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['leden_inactief'] = inactief
        context['wedstrijdklasse_jaar'] = self._huidige_jaar

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class LedenVoorkeurenView(LedenLijstView):

    """ Deze view laat de CWZ de voorkeuren van de zijn leden aanpassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_VOORKEUREN

    def get_queryset(self):
        objs = super().get_queryset()

        nhblid_dict = dict()
        for nhblid in objs:
            nhblid.wedstrijdbogen = list()
            nhblid_dict[nhblid.nhb_nr] = nhblid
        # for

        # zoek de bogen informatie bij elk lid
        for schutterboog in SchutterBoog.objects.\
                filter(voor_wedstrijd=True).\
                select_related('nhblid', 'boogtype').\
                only('nhblid__nhb_nr', 'boogtype__beschrijving'):
            try:
                nhblid = nhblid_dict[schutterboog.nhblid.nhb_nr]
            except KeyError:
                # nhblid niet van deze vereniging
                pass
            else:
                nhblid.wedstrijdbogen.append(schutterboog.boogtype.beschrijving)
        # for

        return objs


class LedenAanmeldenView(UserPassesTestMixin, ListView):

    """ Deze view laat de CWZ zijn ledenlijst zien """

    # class variables shared by all instances
    template_name = TEMPLATE_LEDEN_AANMELDEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        _, functie_nu = rol_get_huidige_functie(self.request)
        return functie_nu and functie_nu.rol == "CWZ"

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Resolver404()

        self.comp = comp
        jeugdgrens = comp.begin_jaar - MAXIMALE_LEEFTIJD_JEUGD

        _, functie_nu = rol_get_huidige_functie(self.request)
        objs = list()

        prev_lkl = None
        prev_wedstrijdleeftijd = 0

        # sorteer jeugd op geboorte jaar en daarna naam
        for obj in NhbLid.objects.\
                filter(bij_vereniging=functie_nu.nhb_ver).\
                filter(geboorte_datum__year__gte=jeugdgrens).\
                order_by('-geboorte_datum__year', 'achternaam', 'voornaam'):

            # de wedstrijdleeftijd voor dit hele jaar
            wedstrijdleeftijd = comp.begin_jaar - obj.geboorte_datum.year
            obj.leeftijd = wedstrijdleeftijd

            # de wedstrijdklasse voor dit hele jaar
            if wedstrijdleeftijd == prev_wedstrijdleeftijd:
                obj.leeftijdsklasse = prev_lkl
            else:
                obj.leeftijdsklasse = LeeftijdsKlasse.objects.filter(
                                max_wedstrijdleeftijd__gte=wedstrijdleeftijd,
                                geslacht='M').order_by('max_wedstrijdleeftijd')[0]
                prev_lkl = obj.leeftijdsklasse
                prev_wedstrijdleeftijd = wedstrijdleeftijd

            objs.append(obj)
        # for

        # sorteer volwassenen op naam
        for obj in NhbLid.objects.\
                        filter(bij_vereniging=functie_nu.nhb_ver).\
                        filter(geboorte_datum__year__lt=jeugdgrens).\
                        order_by('achternaam', 'voornaam'):
            obj.leeftijdsklasse = None
            objs.append(obj)
        # for

        # maak een paar tabellen om database toegangen te verminderen
        nhblid_dict = dict()    # [nhb_nr] = NhbLid
        for nhblid in objs:
            nhblid.wedstrijdbogen = list()
            nhblid_dict[nhblid.nhb_nr] = nhblid
        # for

        ag_dict = dict()        # [schutterboog_pk] = Score
        for score in Score.objects.\
                        select_related('schutterboog').\
                        filter(is_ag=True, afstand_meter=comp.afstand):
            ag = score.waarde / 1000
            ag_dict[score.schutterboog.pk] = ag
        # for

        is_aangemeld_dict = dict()   # [schutterboog.pk] = True/False
        for deelnemer in RegioCompetitieSchutterBoog.objects.\
                select_related('schutterboog', 'deelcompetitie').\
                filter(bij_vereniging=functie_nu.nhb_ver,
                       deelcompetitie__competitie=comp):
            is_aangemeld_dict[deelnemer.schutterboog.pk] = True
        # for

        # zoek de bogen informatie bij elk lid
        # split per schutter-boog
        objs2 = list()
        for schutterboog in SchutterBoog.objects.\
                filter(voor_wedstrijd=True).\
                select_related('nhblid', 'boogtype').\
                order_by('boogtype__volgorde').\
                only('nhblid__nhb_nr', 'boogtype__beschrijving'):
            try:
                nhblid = nhblid_dict[schutterboog.nhblid.nhb_nr]
            except KeyError:
                # schutterboog niet van deze vereniging
                pass
            else:
                # maak een kopie van het nhblid en maak het uniek voor dit boogtype
                obj = copy.copy(nhblid)
                obj.boogtype = schutterboog.boogtype.beschrijving
                obj.check = "lid_%s_boogtype_%s" % (nhblid.nhb_nr, schutterboog.boogtype.pk)

                try:
                    obj.ag = ag_dict[schutterboog.pk]
                except KeyError:
                    obj.ag_18 = AG_NUL

                # kijk of de schutter al aangemeld is
                try:
                    obj.is_aangemeld = is_aangemeld_dict[schutterboog.pk]
                except KeyError:
                    obj.is_aangemeld = False

                objs2.append(obj)
        # for

        return objs2

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        _, functie_nu = rol_get_huidige_functie(self.request)
        context['nhb_ver'] = functie_nu.nhb_ver

        # splits the ledenlijst op in jeugd, senior en inactief
        jeugd = list()
        senior = list()
        for obj in context['object_list']:
            if obj.leeftijdsklasse:
                jeugd.append(obj)
            else:
                senior.append(obj)
        # for

        context['leden_jeugd'] = jeugd
        context['leden_senior'] = senior
        context['comp'] = self.comp
        context['seizoen'] = '%s/%s' % (self.comp.begin_jaar, self.comp.begin_jaar + 1)
        context['aanmelden_url'] = reverse('Vereniging:leden-aanmelden', kwargs={'comp_pk': self.comp.pk})

        menu_dynamics(self.request, context, actief='vereniging')
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de knop 'Geselecteerde schutters aanmelden' wordt gebruikt
            het csrf token is al gecontroleerd
        """
        try:
            comp_pk = int(self.kwargs['comp_pk'][:10])
            comp = Competitie.objects.get(pk=comp_pk)
        except (ValueError, TypeError, Competitie.DoesNotExist):
            raise Resolver404()

        # all checked boxes are in the post request as keys, typically with value 'on'
        for key, _ in request.POST.items():
            # key = 'lid_NNNNNN_boogtype_MM' (of iets anders)
            spl = key.split('_')
            # spl = ('lid', 'NNNNNN', 'boogtype', 'MM')
            if len(spl) == 4 and spl[0] == 'lid' and spl[2] == 'boogtype':
                # dit lijkt ergens op - converteer de getallen (geeft ook input bescherming)
                try:
                    nhblid_pk = int(spl[1])
                    boogtype_pk = int(spl[3])
                except (TypeError, ValueError):
                    # iemand loopt te klooien
                    raise Resolver404()

                # SchutterBoog record met voor_wedstrijd==True moet bestaan
                try:
                    schutterboog = SchutterBoog.objects.get(nhblid=nhblid_pk, boogtype=boogtype_pk)
                except SchutterBoog.DoesNotExist:
                    # iemand loopt te klooien
                    raise Resolver404()
                else:
                    if not schutterboog.voor_wedstrijd:
                        # iemand loopt te klooien
                        raise Resolver404()

                # zoek de aanvangsgemiddelden er bij, indien beschikbaar
                ag = AG_NUL
                for score in Score.objects.filter(schutterboog=schutterboog,
                                                  afstand_meter=comp.afstand,
                                                  is_ag=True):
                    ag = score.waarde / 1000
                # for

                regiocompetitie_schutterboog_aanmelden(comp, schutterboog, ag)

            # else: silently ignore
        # for

        return HttpResponseRedirect(reverse('Vereniging:leden-aanmelden', kwargs={'comp_pk': comp.pk}))


class LijstVerenigingenView(UserPassesTestMixin, ListView):

    """ Via deze view worden kan een BKO, RKO of RCL
          de lijst van verenigingen zien, in zijn werkgebied
    """

    template_name = TEMPLATE_LIJST_VERENIGINGEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu == Rollen.ROL_RKO:
            # toon de lijst van verenigingen in het rayon van de RKO
            # het rayonnummer is verkrijgbaar via de deelcompetitie van de functie
            return NhbVereniging.objects.\
                        select_related('regio', 'regio__rayon').\
                        exclude(regio__regio_nr=100).\
                        filter(regio__rayon=functie_nu.nhb_rayon).\
                        prefetch_related('wedstrijdlocatie_set').\
                        order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO):
            # toon de landelijke lijst
            return NhbVereniging.objects.all().\
                        select_related('regio', 'regio__rayon').\
                        exclude(regio__regio_nr=100).\
                        prefetch_related('wedstrijdlocatie_set').\
                        order_by('regio__regio_nr', 'nhb_nr')

        if rol_nu == Rollen.ROL_IT:
            # landelijke lijst + telling aantal leden
            objs = NhbVereniging.objects.all().\
                        select_related('regio', 'regio__rayon').\
                        exclude(regio__regio_nr=100).\
                        prefetch_related('nhblid_set', 'wedstrijdlocatie_set').\
                        order_by('regio__regio_nr', 'nhb_nr')

            for obj in objs:
                obj.aantal_leden = obj.nhblid_set.count()
            # for
            return objs

        # vul een kleine cache om vele database verzoeken te voorkomen
        cwz_functies = dict()  # [nhb_ver] = Functie()
        for functie in Functie.objects.\
                            filter(rol='CWZ').\
                            select_related('nhb_ver').\
                            prefetch_related('accounts'):
            cwz_functies[functie.nhb_ver.nhb_nr] = functie
        # for

        # toon de lijst van verenigingen in de regio
        if rol_nu == Rollen.ROL_RCL:
            # het regionummer is verkrijgbaar via de deelcompetitie van de functie
            objs = NhbVereniging.objects. \
                filter(regio=functie_nu.nhb_regio). \
                prefetch_related('wedstrijdlocatie_set')
        else:
            # rol_nu == Rollen.ROL_CWZ
            # het regionummer is verkrijgbaar via de vereniging
            objs = NhbVereniging.objects.\
                            filter(regio=functie_nu.nhb_ver.regio).\
                            prefetch_related('wedstrijdlocatie_set')

        for obj in objs:
            try:
                functie_cwz = cwz_functies[obj.nhb_nr]
            except KeyError:
                # deze vereniging heeft geen CWZ functie
                obj.cwzs = list()
            else:
                obj.cwzs = functie_cwz.accounts.all()
        # for
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # voeg de url toe voor de "details" knoppen
        for obj in context['object_list']:
            for loc in obj.wedstrijdlocatie_set.all():
                loc.details_url = reverse('Vereniging:accommodatie-details', kwargs={'locatie_pk': loc.pk})
        # for

        context['toon_rayon'] = True
        context['toon_regio'] = True
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

        if rol_nu in (Rollen.ROL_RCL, Rollen.ROL_CWZ):
            context['toon_rayon'] = False
            context['toon_regio'] = False
            context['toon_cwzs'] = True
            if rol_nu == Rollen.ROL_CWZ:
                menu_actief = 'vereniging'

        menu_dynamics(self.request, context, actief=menu_actief)
        return context


class AccommodatieDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen details van een wedstrijdlocatie gewijzigd worden """

    # class variables shared by all instances
    template_name = TEMPLATE_ACCOMMODATIE_DETAILS

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # zoek de specifieke locatie erbij
        locatie_pk = kwargs['locatie_pk']
        try:
            context['locatie'] = locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        # beschrijving voor de template
        locatie.baan_type_str = BAANTYPE2STR[locatie.baan_type]

        # lijst van verenigingen voor de template
        locatie.nhb_ver = list()
        regio = None
        for ver in locatie.verenigingen.select_related('regio').order_by('nhb_nr'):
            # regio van de locatie afhankelijk van 1e vereniging
            if not regio:
                regio = ver.regio
                context['regio'] = str(regio)
            locatie.nhb_ver.append(str(ver))
        # for

        # terug en opslaan knoppen voor in de template
        if 'is_ver' in kwargs:
            context['terug_url'] = reverse('Vereniging:overzicht')
            context['opslaan_url'] = reverse('Vereniging:vereniging-accommodatie-details', kwargs={'locatie_pk': locatie.pk})
            menu_actief = 'vereniging'
        else:
            context['terug_url'] = reverse('Vereniging:lijst-verenigingen')
            context['opslaan_url'] = reverse('Vereniging:accommodatie-details', kwargs={'locatie_pk': locatie.pk})
            menu_actief = 'hetplein'

        # aantal banen waar uit gekozen kan worden, voor gebruik in de template
        context['banen'] = [nr for nr in range(2, 25)]

        # readonly vlag voor de template: mag de huidige gebruiker wijzigen?
        context['readonly'] = True
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        if functie_nu:
            if rol_nu == Rollen.ROL_CWZ:
                if locatie.verenigingen.filter(nhb_nr=functie_nu.nhb_ver.nhb_nr).count() > 0:
                    # CWZ mag deze vereniging wijzigen
                    context['readonly'] = False
            elif rol_nu == Rollen.ROL_RCL:
                for ver in locatie.verenigingen.all():
                    if ver.regio == functie_nu.nhb_regio:
                        # dit is een vereniging in de regio van de RCL
                        context['readonly'] = False

        menu_dynamics(self.request, context, actief=menu_actief)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruik op de 'opslaan' knop drukt
            op het accommodatie-details formulier.
        """
        # zoek de specifieke locatie erbij
        locatie_pk = kwargs['locatie_pk']
        try:
            locatie = WedstrijdLocatie.objects.get(pk=locatie_pk)
        except WedstrijdLocatie.DoesNotExist:
            raise Resolver404()

        form = AccommodatieDetailsForm(request.POST)
        if not form.is_valid():
            raise Resolver404()

        # TODO: controleer dat de gebruiker deze locatie mag wijzigen

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
        overzicht pagina voor de CWZ. De vlag 'is_ver' resulteer in andere "terug" urls.
    """
    def get_context_data(self, **kwargs):
        kwargs['is_ver'] = True
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        kwargs['is_ver'] = True
        return super().post(request, *args, **kwargs)


# end of file
