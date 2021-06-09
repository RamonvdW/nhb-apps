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
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from Competitie.models import (DeelCompetitie, DeelcompetitieRonde, RegioCompetitieSchutterBoog,
                               LAAG_REGIO, AG_NUL,
                               INSCHRIJF_METHODE_1, INSCHRIJF_METHODE_3,
                               DAGDELEN, DAGDEEL_AFKORTINGEN)
from Competitie.operations import KlasseBepaler
from Plein.menu import menu_dynamics
from Score.models import Score, ScoreHist, SCORE_TYPE_INDIV_AG
from Wedstrijden.models import CompetitieWedstrijd
from .models import SchutterVoorkeuren, SchutterBoog


TEMPLATE_AANMELDEN = 'schutter/bevestig-aanmelden.dtl'
TEMPLATE_SCHIETMOMENTEN = 'schutter/schietmomenten.dtl'


class RegiocompetitieAanmeldenBevestigView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een schutter zich aanmelden voor een competitie """

    template_name = TEMPLATE_AANMELDEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            schutterboog_pk = int(kwargs['schutterboog_pk'][:10])

            schutterboog = (SchutterBoog
                            .objects
                            .select_related('nhblid')
                            .get(pk=schutterboog_pk))

            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie', 'nhb_regio')
                        .get(pk=deelcomp_pk))

        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except (SchutterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase < 'B' or deelcomp.competitie.fase >= 'F':
            raise Http404('Verkeerde competitie fase')

        # controleer dat schutterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        account = self.request.user
        nhblid = account.nhblid_set.all()[0]      # ROL_SCHUTTER geeft bescherming tegen geen nhblid
        if (schutterboog.nhblid != nhblid
                or deelcomp.laag != LAAG_REGIO
                or deelcomp.nhb_regio != nhblid.bij_vereniging.regio):
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        schutterboog=schutterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        # bepaal in welke wedstrijdklasse de schutter komt
        age = schutterboog.nhblid.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)

        # haal AG op, indien aanwezig
        scores = Score.objects.filter(schutterboog=schutterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      afstand_meter=deelcomp.competitie.afstand)
        ag = AG_NUL
        if len(scores):
            score = scores[0]
            ag = score.waarde / 1000
            hist = ScoreHist.objects.filter(score=score).order_by('-when')
            if len(hist):
                context['ag_hist'] = hist[0]
        context['ag'] = ag

        aanmelding = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            schutterboog=schutterboog,
                            ag_voor_indiv=AG_NUL)

        bepaler = KlasseBepaler(deelcomp.competitie)
        bepaler.bepaal_klasse_deelnemer(aanmelding)
        context['wedstrijdklasse'] = aanmelding.klasse.indiv.beschrijving
        context['is_klasse_onbekend'] = aanmelding.klasse.indiv.is_onbekend
        del aanmelding

        udvl = deelcomp.competitie.uiterste_datum_lid       # uiterste datum van lidmaatschap
        dvl = schutterboog.nhblid.sinds_datum               # datum van lidmaatschap

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             dvl < udvl
                             and deelcomp.competitie.fase == 'B')
        context['mag_team_schieten'] = mag_team_schieten

        # bepaal de inschrijfmethode voor deze regio
        methode = deelcomp.inschrijf_methode

        context['deelcomp'] = deelcomp
        context['schutterboog'] = schutterboog
        context['voorkeuren'], _ = SchutterVoorkeuren.objects.get_or_create(nhblid=nhblid)
        context['bevestig_url'] = reverse('Schutter:aanmelden',
                                          kwargs={'schutterboog_pk': schutterboog.pk,
                                                  'deelcomp_pk': deelcomp.pk})

        if methode == INSCHRIJF_METHODE_1:
            pks = list()
            for ronde in (DeelcompetitieRonde
                          .objects
                          .select_related('plan')
                          .filter(deelcompetitie=deelcomp)):
                # toon de HWL alle wedstrijden in de regio, dus alle clusters
                pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
            # for

            wedstrijden = (CompetitieWedstrijd
                           .objects
                           .filter(pk__in=pks)
                           .select_related('vereniging')
                           .order_by('datum_wanneer',
                                     'tijd_begin_wedstrijd'))
            context['wedstrijden'] = wedstrijden

        if methode == INSCHRIJF_METHODE_3:
            context['dagdelen'] = DAGDELEN
            if deelcomp.toegestane_dagdelen != '':
                context['dagdelen'] = list()
                for dagdeel in DAGDELEN:
                    # dagdeel = tuple(code, beschrijving)
                    # code = GN / AV / ZA / ZO / WE
                    if dagdeel[0] in deelcomp.toegestane_dagdelen:
                        context['dagdelen'].append(dagdeel)
                # for

        if deelcomp.competitie.afstand == '18':
            if schutterboog.boogtype.afkorting in ('R', 'BB'):
                context['show_dt'] = True

        menu_dynamics(self.request, context, actief='schutter-profiel')
        return context


class RegiocompetitieAanmeldenView(View):

    """ Deze class wordt gebruikt om een schutterboog in te schrijven voor een regiocompetitie
        methode 1 / 2 : direct geaccepteerd

        methode 3: nhblid heeft voorkeuren opgegeven: dagdeel, team schieten, opmerking
    """
    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn profiel pagina
            de knop Aanmelden gebruikt voor een specifieke regiocompetitie en boogtype.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        nhblid = None
        account = request.user
        if account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if not (nhblid.is_actief_lid and nhblid.bij_vereniging):
                    nhblid = None
        if not nhblid:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            schutterboog_pk = int(kwargs['schutterboog_pk'][:10])

            schutterboog = (SchutterBoog
                            .objects
                            .select_related('nhblid')
                            .get(pk=schutterboog_pk))

            deelcomp = (DeelCompetitie
                        .objects
                        .select_related('competitie',
                                        'nhb_regio')
                        .get(pk=deelcomp_pk))
        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except (SchutterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record(s)
            raise Http404('Sporter of competitie niet gevonden')

        # controleer dat de competitie aanmeldingen accepteert
        deelcomp.competitie.bepaal_fase()
        if deelcomp.competitie.fase < 'B' or deelcomp.competitie.fase >= 'F':
            raise Http404('Verkeerde competitie fase')

        # controleer dat schutterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        if (schutterboog.nhblid != nhblid
                or deelcomp.laag != LAAG_REGIO
                or deelcomp.nhb_regio != nhblid.bij_vereniging.regio):
            raise Http404('Geen valide combinatie')

        # voorkom dubbele aanmelding
        if (RegioCompetitieSchutterBoog
                .objects
                .filter(deelcompetitie=deelcomp,
                        schutterboog=schutterboog)
                .count() > 0):
            # al aangemeld - zie niet hier moeten zijn gekomen
            raise Http404('Sporter is al aangemeld')

        # urlconf parameters geaccepteerd

        # bepaal de inschrijfmethode voor deze regio
        methode = deelcomp.inschrijf_methode

        # bepaal in welke wedstrijdklasse de schutter komt
        age = schutterboog.nhblid.bereken_wedstrijdleeftijd(deelcomp.competitie.begin_jaar + 1)

        aanmelding = RegioCompetitieSchutterBoog(
                            deelcompetitie=deelcomp,
                            schutterboog=schutterboog,
                            bij_vereniging=schutterboog.nhblid.bij_vereniging,
                            ag_voor_indiv=AG_NUL,
                            ag_voor_team=AG_NUL,
                            ag_voor_team_mag_aangepast_worden=True)

        # haal AG op, indien aanwezig
        scores = Score.objects.filter(schutterboog=schutterboog,
                                      type=SCORE_TYPE_INDIV_AG,
                                      afstand_meter=deelcomp.competitie.afstand)
        if len(scores):
            score = scores[0]
            ag = score.waarde / 1000
            aanmelding.ag_voor_indiv = ag
            aanmelding.ag_voor_team = ag
            if ag > 0.000:
                aanmelding.ag_voor_team_mag_aangepast_worden = False

        bepaler = KlasseBepaler(deelcomp.competitie)
        bepaler.bepaal_klasse_deelnemer(aanmelding)

        udvl = deelcomp.competitie.uiterste_datum_lid       # uiterste datum van lidmaatschap
        dvl = schutterboog.nhblid.sinds_datum               # datum van lidmaatschap

        # geen aspirant, op tijd lid en op tijd aangemeld?
        mag_team_schieten = (deelcomp.regio_organiseert_teamcompetitie and
                             age > MAXIMALE_WEDSTRIJDLEEFTIJD_ASPIRANT and
                             dvl < udvl
                             and deelcomp.competitie.fase == 'B')

        # kijk of de schutter met een team mee wil schieten voor deze competitie
        if mag_team_schieten and request.POST.get('wil_in_team', '') != '':
            aanmelding.inschrijf_voorkeur_team = True

        # kijk of er velden van een formulier bij zitten
        if methode == INSCHRIJF_METHODE_3:
            aanmelding.inschrijf_voorkeur_dagdeel = ''

            dagdeel = request.POST.get('dagdeel', '')
            if dagdeel in DAGDEEL_AFKORTINGEN:
                if dagdeel in deelcomp.toegestane_dagdelen or deelcomp.toegestane_dagdelen == '':
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

        return HttpResponseRedirect(reverse('Schutter:profiel'))


class RegiocompetitieAfmeldenView(View):

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn profiel pagina
            de knop Uitschrijven gebruikt voor een specifieke regiocompetitie.
        """
        # voorkom misbruik: ingelogd als niet geblokkeerd nhblid vereist
        nhblid = None
        account = request.user
        if account.is_authenticated:
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                if not (nhblid.is_actief_lid and nhblid.bij_vereniging):
                    nhblid = None
        if not nhblid:
            raise Http404('Sporter niet gevonden')

        # converteer en doe eerste controle op de parameters
        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])     # afkappen geeft bescherming
            inschrijving = RegioCompetitieSchutterBoog.objects.get(pk=deelnemer_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Http404()
        except RegioCompetitieSchutterBoog.DoesNotExist:
            # niet bestaand record
            raise Http404('Inschrijving niet gevonden')

        # controleer dat deze inschrijving bij het nhblid hoort
        if inschrijving.schutterboog.nhblid != nhblid:
            raise PermissionDenied()

        # TODO: controleer de fase van de competitie. Na bepaalde datum niet meer uit kunnen schrijven??

        # schrijf de schutter uit
        inschrijving.delete()

        return HttpResponseRedirect(reverse('Schutter:profiel'))


class SchutterSchietmomentenView(UserPassesTestMixin, TemplateView):

    template_name = TEMPLATE_SCHIETMOMENTEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) in (Rollen.ROL_SCHUTTER, Rollen.ROL_HWL)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelnemer_pk = int(self.kwargs['deelnemer_pk'][:6])       # afkappen geeft veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('deelcompetitie',
                                         'deelcompetitie__competitie')
                         .get(pk=deelnemer_pk,
                              deelcompetitie__inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        context['deelnemer'] = deelnemer

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        if rol_nu == Rollen.ROL_SCHUTTER:
            if self.request.user != deelnemer.schutterboog.nhblid.account:
                raise PermissionDenied()
        else:
            # HWL: sporter moet lid zijn van zijn vereniging
            if deelnemer.bij_vereniging != functie_nu.nhb_ver:
                raise PermissionDenied('Sporter is niet van jouw vereniging')

        # zoek alle dagdelen erbij
        pks = list()
        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('deelcompetitie',
                                      'plan')
                      .prefetch_related('plan__wedstrijden')
                      .filter(deelcompetitie=deelnemer.deelcompetitie)):
            pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
        # for

        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))

        context['wedstrijden'] = wedstrijden

        keuze = list(deelnemer.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True))
        for wedstrijd in wedstrijden:
            wedstrijd.is_gekozen = (wedstrijd.pk in keuze)
        # for

        context['url_opslaan'] = reverse('Schutter:schietmomenten',
                                         kwargs={'deelnemer_pk': deelnemer.pk})

        if rol_nu == Rollen.ROL_SCHUTTER:
            context['url_terug'] = reverse('Schutter:profiel')
        else:
            context['url_terug'] = reverse('Vereniging:schietmomenten',
                                           kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})

        menu_dynamics(self.request, context, actief='schutter-profiel')
        return context

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn
            schietmomenten-pagina de knop Opslaan gebruikt.
        """

        try:
            deelnemer_pk = int(kwargs['deelnemer_pk'][:6])       # afkappen geeft veiligheid
            deelnemer = (RegioCompetitieSchutterBoog
                         .objects
                         .select_related('deelcompetitie',
                                         'deelcompetitie__competitie')
                         .get(pk=deelnemer_pk,
                              deelcompetitie__inschrijf_methode=INSCHRIJF_METHODE_1))
        except (ValueError, TypeError, RegioCompetitieSchutterBoog.DoesNotExist):
            raise Http404('Inschrijving niet gevonden')

        rol_nu, functie_nu = rol_get_huidige_functie(request)

        # controleer dat ingelogde gebruiker deze wijziging mag maken
        if rol_nu == Rollen.ROL_SCHUTTER:
            if request.user != deelnemer.schutterboog.nhblid.account:
                raise PermissionDenied()
        else:
            # HWL: sporter moet lid zijn van zijn vereniging
            if deelnemer.bij_vereniging != functie_nu.nhb_ver:
                raise PermissionDenied('Sporter is niet van jouw vereniging')

        # zoek alle wedstrijden erbij
        pks = list()
        for ronde in (DeelcompetitieRonde
                      .objects
                      .select_related('deelcompetitie',
                                      'plan')
                      .prefetch_related('plan__wedstrijden')
                      .filter(deelcompetitie=deelnemer.deelcompetitie)):
            pks.extend(ronde.plan.wedstrijden.values_list('pk', flat=True))
        # for

        # zoek alle wedstrijden erbij
        wedstrijden = (CompetitieWedstrijd
                       .objects
                       .filter(pk__in=pks)
                       .select_related('vereniging')
                       .order_by('datum_wanneer',
                                 'tijd_begin_wedstrijd'))

        keuze = list(deelnemer.inschrijf_gekozen_wedstrijden.values_list('pk', flat=True))
        keuze_add = list()
        aanwezig = len(keuze)

        for wedstrijd in wedstrijden:
            param = 'wedstrijd_%s' % wedstrijd.pk
            if request.POST.get(param, '') != '':
                # deze wedstrijd is gekozen
                if wedstrijd.pk in keuze:
                    # al gekozen, dus behouden
                    keuze.remove(wedstrijd.pk)
                else:
                    # toevoegen
                    keuze_add.append(wedstrijd.pk)
        # for

        # alle overgebleven wedstrijden zijn ongewenst
        aanwezig -= len(keuze)
        deelnemer.inschrijf_gekozen_wedstrijden.remove(*keuze)

        # controleer dat er maximaal 7 momenten gekozen worden
        if aanwezig + len(keuze_add) > 7:
            # begrens het aantal toe te voegen wedstrijden
            keuze_add = keuze_add[:7 - aanwezig]

        deelnemer.inschrijf_gekozen_wedstrijden.add(*keuze_add)

        if rol_nu == Rollen.ROL_SCHUTTER:
            url = reverse('Schutter:profiel')
        else:
            url = reverse('Vereniging:schietmomenten',
                          kwargs={'deelcomp_pk': deelnemer.deelcompetitie.pk})

        return HttpResponseRedirect(url)

# end of file
