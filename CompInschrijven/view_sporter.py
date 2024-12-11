# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View, TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from BasisTypen.definities import MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from Competitie.definities import INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3, DAGDELEN, DAGDEEL_AFKORTINGEN
from Competitie.models import CompetitieMatch, Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog
from Competitie.operations import KlasseBepaler
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from Score.definities import AG_NUL, AG_DOEL_INDIV, AG_DOEL_TEAM
from Score.models import AanvangsgemiddeldeHist, Aanvangsgemiddelde
from Sporter.models import SporterVoorkeuren, SporterBoog, get_sporter
from Sporter.operations import get_sporter_voorkeuren
from decimal import Decimal


TEMPLATE_SPORTER_AANMELDEN = 'compinschrijven/sporter-bevestig-aanmelden.dtl'


class RegiocompetitieAanmeldenBevestigView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zich aanmelden voor een competitie """

    template_name = TEMPLATE_SPORTER_AANMELDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])           # afkappen voor de veiligheid
            sporterboog_pk = int(kwargs['sporterboog_pk'][:10])     # afkappen voor de veiligheid

            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))

            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'regio')
                        .get(pk=deelcomp_pk))

        except (ValueError, KeyError, SporterBoog.DoesNotExist, Regiocompetitie.DoesNotExist):
            # niet bestaand record
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase_indiv < 'C' or comp.fase_indiv >= 'G':
            raise Http404('Verkeerde competitie fase')

        # controleer dat sporterboog bij de ingelogde gebruiker hoort;
        # controleer dat regiocompetitie bij de juist regio hoort
        account = get_account(self.request)     # ROL_SPORTER geeft bescherming tegen geen Sporter
        sporter = get_sporter(account)
        if sporterboog.sporter != sporter or deelcomp.regio != sporter.bij_vereniging.regio:
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegiocompetitieSporterBoog
                .objects
                .filter(regiocompetitie=deelcomp,
                        sporterboog=sporterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        voorkeuren = get_sporter_voorkeuren(sporter)
        if voorkeuren.wedstrijd_geslacht_gekozen:
            wedstrijdgeslacht = voorkeuren.wedstrijd_geslacht   # M/V
        else:
            wedstrijdgeslacht = sporter.geslacht                # M/V/X

        # bepaal in welke wedstrijdklasse de sporter komt
        age = sporterboog.sporter.bereken_wedstrijdleeftijd_wa(comp.begin_jaar + 1)

        # haal AG op, indien aanwezig
        ags = Aanvangsgemiddelde.objects.filter(sporterboog=sporterboog,
                                                doel=AG_DOEL_INDIV,
                                                afstand_meter=comp.afstand)
        ag = Decimal(AG_NUL)
        if len(ags):
            ag = ags[0].waarde
            hist = AanvangsgemiddeldeHist.objects.filter(ag=ags[0]).order_by('-when')
            if len(hist):
                context['ag_hist'] = hist[0]
        context['ag'] = ag

        aanmelding = RegiocompetitieSporterBoog(
                            regiocompetitie=deelcomp,
                            sporterboog=sporterboog,
                            ag_voor_indiv=ag)

        bepaler = KlasseBepaler(comp)
        try:
            bepaler.bepaal_klasse_deelnemer(aanmelding, wedstrijdgeslacht)
        except LookupError as exc:
            raise Http404(str(exc))

        context['wedstrijdklasse'] = aanmelding.indiv_klasse.beschrijving
        context['is_klasse_onbekend'] = aanmelding.indiv_klasse.is_onbekend
        del aanmelding

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             comp.fase_indiv == 'C')
        context['mag_team_schieten'] = mag_team_schieten

        # bepaal de inschrijfmethode voor deze regio
        methode = deelcomp.inschrijf_methode

        context['deelcomp'] = deelcomp
        context['sporterboog'] = sporterboog
        context['voorkeuren'], _ = SporterVoorkeuren.objects.get_or_create(sporter=sporter)
        context['bevestig_url'] = reverse('CompInschrijven:aanmelden',
                                          kwargs={'sporterboog_pk': sporterboog.pk,
                                                  'deelcomp_pk': deelcomp.pk})

        if methode == INSCHRIJF_METHODE_1:
            # toon de sporter alle wedstrijden in de regio, dus alle clusters
            pks = list()
            for ronde in (RegiocompetitieRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(regiocompetitie=deelcomp)):
                pks.extend(ronde.matches.values_list('pk', flat=True))
            # for

            wedstrijden = (CompetitieMatch
                           .objects
                           .filter(pk__in=pks)
                           .exclude(vereniging__isnull=True)  # voorkom wedstrijd niet toegekend aan vereniging
                           .select_related('vereniging')
                           .order_by('datum_wanneer',
                                     'tijd_begin_wedstrijd'))

            # splits de wedstrijden op naar in-cluster en out-of-cluster
            ver = sporterboog.sporter.bij_vereniging
            ver_in_hwl_cluster = dict()  # [ver_nr] = True/False
            for cluster in (ver
                            .clusters
                            .prefetch_related('vereniging_set')
                            .filter(gebruik=comp.afstand)
                            .all()):
                ver_nrs = list(cluster.vereniging_set.values_list('ver_nr', flat=True))
                for ver_nr in ver_nrs:
                    ver_in_hwl_cluster[ver_nr] = True
                # for
            # for

            wedstrijden1 = list()
            wedstrijden2 = list()
            for wedstrijd in wedstrijden:
                try:
                    in_cluster = ver_in_hwl_cluster[wedstrijd.vereniging.ver_nr]
                except KeyError:
                    in_cluster = False

                if in_cluster:
                    wedstrijden1.append(wedstrijd)
                else:
                    wedstrijden2.append(wedstrijd)
            # for

            if len(wedstrijden1):
                context['wedstrijden_1'] = wedstrijden1
                context['wedstrijden_2'] = wedstrijden2
            else:
                context['wedstrijden_1'] = wedstrijden2

        if methode == INSCHRIJF_METHODE_3:
            context['dagdelen'] = DAGDELEN
            if deelcomp.toegestane_dagdelen != '':
                dagdelen_spl = deelcomp.toegestane_dagdelen.split(',')
                context['dagdelen'] = list()
                for dagdeel in DAGDELEN:
                    # dagdeel = tuple(code, beschrijving)
                    # code = GN / AV / ZA / ZO / WE
                    if dagdeel[0] in dagdelen_spl:
                        context['dagdelen'].append(dagdeel)
                # for

        # FUTURE: eigen blazoen is ook mogelijk voor 25m (4-spot)
        if comp.is_indoor():
            if sporterboog.boogtype.afkorting in ('R', 'BB'):
                context['eigen_blazoen'] = True

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Aanmelden ' + comp.beschrijving.replace(' competitie', ''))
        )

        return context


class RegiocompetitieAanmeldenView(UserPassesTestMixin, View):

    """ Deze class wordt gebruikt om een sporterboog in te schrijven voor een regiocompetitie
        methode 1 of 2: direct geaccepteerd

        methode 3: sporter heeft voorkeuren opgegeven: dagdeel, team schieten, opmerking
    """

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de sporter op zijn profiel pagina
            de knop Aanmelden gebruikt voor een specifieke regiocompetitie en boogtype.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerde sporter vereist
        account = get_account(request)
        sporter = get_sporter(account)
        if sporter:
            if not (sporter.is_actief_lid and sporter.bij_vereniging):
                sporter = None

        if not sporter:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])           # afkappen voor de veiligheid
            sporterboog_pk = int(kwargs['sporterboog_pk'][:10])     # afkappen voor de veiligheid

            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))

            deelcomp = (Regiocompetitie
                        .objects
                        .select_related('competitie',
                                        'regio')
                        .get(pk=deelcomp_pk))
        except (ValueError, KeyError, SporterBoog.DoesNotExist, Regiocompetitie.DoesNotExist):
            # niet bestaand record(s)
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        comp = deelcomp.competitie
        comp.bepaal_fase()
        if comp.fase_indiv < 'C' or comp.fase_indiv >= 'G':
            raise Http404('Verkeerde competitie fase')

        # controleer dat sporterboog bij de ingelogde gebruiker hoort;
        # controleer dat regiocompetitie bij de juist regio hoort
        if sporterboog.sporter != sporter or deelcomp.regio != sporter.bij_vereniging.regio:
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegiocompetitieSporterBoog
                .objects
                .filter(regiocompetitie=deelcomp,
                        sporterboog=sporterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        now = timezone.now()
        when_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        voorkeuren = get_sporter_voorkeuren(sporter, mag_database_wijzigen=True)
        if voorkeuren.wedstrijd_geslacht_gekozen:
            wedstrijdgeslacht = voorkeuren.wedstrijd_geslacht   # M/V
        else:
            wedstrijdgeslacht = sporter.geslacht                # M/V/X

        # bepaal de inschrijfmethode voor deze regio
        methode = deelcomp.inschrijf_methode

        # bepaal in welke wedstrijdklasse de sporter komt
        age = sporterboog.sporter.bereken_wedstrijdleeftijd_wa(deelcomp.competitie.begin_jaar + 1)

        msg = '[%s] Zelfstandig aangemeld\n' % when_str
        aanmelding = RegiocompetitieSporterBoog(
                            regiocompetitie=deelcomp,
                            sporterboog=sporterboog,
                            bij_vereniging=sporterboog.sporter.bij_vereniging,
                            ag_voor_indiv=AG_NUL,
                            ag_voor_team=AG_NUL,
                            ag_voor_team_mag_aangepast_worden=True,
                            aangemeld_door=account,
                            logboekje=msg)

        # haal AG op, indien aanwezig
        ags = Aanvangsgemiddelde.objects.filter(sporterboog=sporterboog,
                                                doel=AG_DOEL_INDIV,
                                                afstand_meter=deelcomp.competitie.afstand)
        if len(ags):
            ag = ags[0]
            aanmelding.ag_voor_indiv = ag.waarde
            aanmelding.ag_voor_team = ag.waarde
            if ag.waarde > 0.000:
                aanmelding.ag_voor_team_mag_aangepast_worden = False

        if aanmelding.ag_voor_team_mag_aangepast_worden:
            # geen vastgesteld AG - kijk of we nog een handmatig AG kunnen vinden
            ag_hist = (AanvangsgemiddeldeHist
                       .objects
                       .filter(ag__sporterboog=sporterboog,
                               ag__doel=AG_DOEL_TEAM,
                               ag__afstand_meter=deelcomp.competitie.afstand)
                       .order_by('-when')      # nieuwste eerst
                       .first())

            if ag_hist:
                # iemand heeft een AG ingevoerd voor de teamcompetitie
                # let op: dit kan van lang geleden zijn
                ag = ag_hist.ag
                aanmelding.ag_voor_team = ag.waarde
                aanmelding.ag_voor_team_mag_aangepast_worden = True

        bepaler = KlasseBepaler(deelcomp.competitie)
        try:
            bepaler.bepaal_klasse_deelnemer(aanmelding, wedstrijdgeslacht)
        except LookupError as exc:
            raise Http404(str(exc))

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             deelcomp.competitie.fase_indiv == 'C')

        # kijk of de sporter met een team mee wil schieten voor deze competitie
        if mag_team_schieten and request.POST.get('wil_in_team', '') != '':
            aanmelding.inschrijf_voorkeur_team = True

        if request.POST.get('geen_rk', '') != '':
            # sporter wil zich alvast afmelden voor het RK
            aanmelding.inschrijf_voorkeur_rk_bk = False
            msg = '[%s] Bij inschrijving geen voorkeur voor RK\n' % when_str
            aanmelding.logboekje += msg

        # kijk of er velden van een formulier bij zitten
        if methode == INSCHRIJF_METHODE_3:
            aanmelding.inschrijf_voorkeur_dagdeel = ''
            dagdelen_spl = deelcomp.toegestane_dagdelen.split(',')

            dagdeel = request.POST.get('dagdeel', '')
            if dagdeel in DAGDEEL_AFKORTINGEN:
                if deelcomp.toegestane_dagdelen == '' or dagdeel in dagdelen_spl:
                    aanmelding.inschrijf_voorkeur_dagdeel = dagdeel

            if aanmelding.inschrijf_voorkeur_dagdeel == '':
                # dagdeel is verplicht
                raise Http404('Verzoek is niet compleet')

        opmerking = request.POST.get('opmerking', '')
        if len(opmerking) > 500:
            opmerking = opmerking[:500]     # moet afkappen, anders database foutmelding
        aanmelding.inschrijf_notitie = opmerking

        aanmelding.save()

        if methode == INSCHRIJF_METHODE_1:
            pks = list()
            for ronde in (RegiocompetitieRonde
                          .objects
                          .prefetch_related('matches')
                          .filter(regiocompetitie=deelcomp)):
                # sta alle wedstrijden in de regio toe, dus alle clusters
                pks.extend(ronde.matches.values_list('pk', flat=True))
            # for
            wedstrijden = list()
            for pk in pks:
                key = 'wedstrijd_%s' % pk
                if request.POST.get(key, '') != '':
                    wedstrijden.append(pk)
            # for
            aanmelding.inschrijf_gekozen_matches.set(wedstrijden)

        return HttpResponseRedirect(reverse('Sporter:profiel'))


class RegiocompetitieAfmeldenView(View):

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de sporter op zijn profiel pagina
            de knop Uitschrijven gebruikt voor een specifieke regiocompetitie.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd sporter vereist
        sporter = None
        if request.user.is_authenticated:
            account = get_account(request)
            sporter = get_sporter(account)
            if sporter:
                if not (sporter.is_actief_lid and sporter.bij_vereniging):
                    sporter = None
        if not sporter:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])     # afkappen voor de veiligheid
            deelnemer = (RegiocompetitieSporterBoog
                         .objects
                         .select_related('regiocompetitie__competitie',
                                         'sporterboog__sporter')
                         .get(pk=deelnemer_pk))
        except (ValueError, KeyError, RegiocompetitieSporterBoog.DoesNotExist):
            # niet bestaand record
            raise Http404('Inschrijving niet gevonden')

        # controleer dat deze inschrijving bij het sporter hoort
        if deelnemer.sporterboog.sporter != sporter:
            raise PermissionDenied('Je kan alleen jezelf uitschrijven')

        # controleer de fase van de competitie
        comp = deelnemer.regiocompetitie.competitie
        comp.bepaal_fase()
        if comp.fase_indiv != 'C':
            raise Http404('Competitie is in de verkeerde fase')

        # schrijf de sporter uit
        try:
            deelnemer.delete()
        except RegiocompetitieSporterBoog.DoesNotExist:
            # silently ignore (kan voorkomen bij parallelle posts)
            pass

        return HttpResponseRedirect(reverse('Sporter:profiel'))


# end of file
