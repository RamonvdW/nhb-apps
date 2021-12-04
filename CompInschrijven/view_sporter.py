# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import View, TemplateView
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT
from Functie.rol import Rollen, rol_get_huidige
from Competitie.models import (DeelCompetitie, DeelcompetitieRonde, RegioCompetitieSchutterBoog,
                               LAAG_REGIO, AG_NUL,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3,
                               DAGDELEN, DAGDEEL_AFKORTINGEN)
from Competitie.operations import KlasseBepaler
from Plein.menu import menu_dynamics
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG
from Wedstrijden.models import CompetitieWedstrijd
from Sporter.models import SporterVoorkeuren, SporterBoog
from decimal import Decimal


TEMPLATE_SPORTER_AANMELDEN = 'compinschrijven/sporter-bevestig-aanmelden.dtl'


class RegiocompetitieAanmeldenBevestigView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zich aanmelden voor een competitie """

    template_name = TEMPLATE_SPORTER_AANMELDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en rol Sporter gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SPORTER

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            sporterboog_pk = int(kwargs['sporterboog_pk'][:10])

            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))

            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio')
                        .get(pk=deelcomp_pk))

        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except (SporterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase < 'B' or deelcomp.competitie.fase >= 'F':
            raise Http404('Verkeerde competitie fase')

        # controleer dat sporterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        account = self.request.user
        sporter = account.sporter_set.all()[0]      # ROL_SCHUTTER geeft bescherming tegen geen nhblid
        if (sporterboog.sporter != sporter
                or deelcomp.laag != LAAG_REGIO
                or deelcomp.nhb_regio != sporter.bij_vereniging.regio):
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        sporterboog=sporterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        # bepaal in welke wedstrijdklasse de sporter komt
        age = sporterboog.sporter.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)

        # haal AG op, indien aanwezig
        scores = Score.objects.filter(sporterboog=sporterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      afstand_meter=deelcomp.competitie.afstand)
        ag = Decimal(AG_NUL)
        if len(scores):
            score = scores[0]
            ag = Decimal(score.waarde) / 1000
            hist = ScoreHist.objects.filter(score=score).order_by('-when')
            if len(hist):
                context['ag_hist'] = hist[0]
        context['ag'] = ag

        aanmelding = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            sporterboog=sporterboog,
                            ag_voor_indiv=ag)

        bepaler = KlasseBepaler(deelcomp.competitie)
        try:
            bepaler.bepaal_klasse_deelnemer(aanmelding)
        except LookupError as exc:
            raise Http404(str(exc))

        context['wedstrijdklasse'] = aanmelding.klasse.indiv.beschrijving
        context['is_klasse_onbekend'] = aanmelding.klasse.indiv.is_onbekend
        del aanmelding

        udvl = deelcomp.competitie.uiterste_datum_lid       # uiterste datum van lidmaatschap
        dvl = sporterboog.sporter.sinds_datum               # datum van lidmaatschap

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             dvl < udvl
                             and deelcomp.competitie.fase == 'B')
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
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=deelcomp)):
                pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for

            wedstrijden = (CompetitieWedstrijd
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
                            .prefetch_related('nhbvereniging_set')
                            .filter(gebruik=deelcomp.competitie.afstand)
                            .all()):
                ver_nrs = list(cluster.nhbvereniging_set.values_list('ver_nr', flat=True))
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

        if deelcomp.competitie.afstand == '18':
            if sporterboog.boogtype.afkorting in ('R', 'BB'):
                context['show_dt'] = True

        menu_dynamics(self.request, context, actief='sporter-profiel')
        return context


class RegiocompetitieAanmeldenView(View):

    """ Deze class wordt gebruikt om een sporterboog in te schrijven voor een regiocompetitie
        methode 1 / 2 : direct geaccepteerd

        methode 3: nhblid heeft voorkeuren opgegeven: dagdeel, team schieten, opmerking
    """
    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de sporter op zijn profiel pagina
            de knop Aanmelden gebruikt voor een specifieke regiocompetitie en boogtype.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        sporter = None
        account = request.user
        if account.is_authenticated:
            if account.sporter_set.count() > 0:
                sporter = account.sporter_set.all()[0]
                if not (sporter.is_actief_lid and sporter.bij_vereniging):
                    sporter = None
        if not sporter:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            sporterboog_pk = int(kwargs['sporterboog_pk'][:10])

            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .get(pk=sporterboog_pk))

            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio')
                        .get(pk=deelcomp_pk))
        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except (SporterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record(s)
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase < 'B' or deelcomp.competitie.fase >= 'F':
            raise Http404('Verkeerde competitie fase')

        # controleer dat sporterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        if (sporterboog.sporter != sporter
                or deelcomp.laag != LAAG_REGIO
                or deelcomp.nhb_regio != sporter.bij_vereniging.regio):
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        sporterboog=sporterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        # bepaal de inschrijfmethode voor deze regio
        methode = deelcomp.inschrijf_methode

        # bepaal in welke wedstrijdklasse de sporter komt
        age = sporterboog.sporter.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)

        aanmelding = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            sporterboog=sporterboog,
                            bij_vereniging=sporterboog.sporter.bij_vereniging,
                            ag_voor_indiv=AG_NUL,
                            ag_voor_team=AG_NUL,
                            ag_voor_team_mag_aangepast_worden=True)

        # haal AG op, indien aanwezig
        scores = Score.objects.filter(sporterboog=sporterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      afstand_meter=deelcomp.competitie.afstand)
        if len(scores):
            score = scores[0]
            ag = Decimal(score.waarde) / 1000
            aanmelding.ag_voor_indiv = ag
            aanmelding.ag_voor_team = ag
            if ag > 0.000:
                aanmelding.ag_voor_team_mag_aangepast_worden = False

        bepaler = KlasseBepaler(deelcomp.competitie)
        try:
            bepaler.bepaal_klasse_deelnemer(aanmelding)
        except LookupError as exc:
            raise Http404(str(exc))

        udvl = deelcomp.competitie.uiterste_datum_lid       # uiterste datum van lidmaatschap
        dvl = sporterboog.sporter.sinds_datum               # datum van lidmaatschap

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             dvl < udvl
                             and deelcomp.competitie.fase == 'B')

        # kijk of de sporter met een team mee wil schieten voor deze competitie
        if mag_team_schieten and request.POST.get('wil_in_team', '') != '':
            aanmelding.inschrijf_voorkeur_team = True

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
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=deelcomp)):
                # sta alle wedstrijden in de regio toe, dus alle clusters
                pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for
            wedstrijden = list()
            for pk in pks:
                key = 'wedstrijd_%s' % pk
                if request.POST.get(key, '') != '':
                    wedstrijden.append(pk)
            # for
            aanmelding.inschrijf_gekozen_wedstrijden.set(wedstrijden)

        return HttpResponseRedirect(reverse('Sporter:profiel'))


class RegiocompetitieAfmeldenView(View):

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de sporter op zijn profiel pagina
            de knop Uitschrijven gebruikt voor een specifieke regiocompetitie.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        sporter = None
        account = request.user
        if account.is_authenticated:
            if account.sporter_set.count() > 0:
                sporter = account.sporter_set.all()[0]
                if not (sporter.is_actief_lid and sporter.bij_vereniging):
                    sporter = None
        if not sporter:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])     # afkappen geeft bescherming
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('deelcompetitie__competitie',
                                         'sporterboog__sporter')
                         .get(pk=deelnemer_pk))
        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except RegioCompetitieSchutterBoog.DoesNotExist:
            # niet bestaand record
            raise Http404('Inschrijving niet gevonden')

        # controleer dat deze inschrijving bij het nhblid hoort
        if deelnemer.sporterboog.sporter != sporter:
            raise PermissionDenied('Je kan alleen jezelf uitschrijven')

        # controleer de fase van de competitie
        comp = deelnemer.deelcompetitie.competitie
        comp.bepaal_fase()
        if comp.fase != 'B':
            raise Http404('Competitie is in de verkeerde fase')

        # schrijf de sporter uit
        deelnemer.delete()

        return HttpResponseRedirect(reverse('Sporter:profiel'))


# end of file
