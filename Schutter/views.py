# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from BasisTypen.models import BoogType
from Competitie.models import CompetitieKlasse, DeelCompetitie, RegioCompetitieSchutterBoog,\
                              LAAG_REGIO, AG_NUL, regiocompetitie_schutterboog_aanmelden
from Records.models import IndivRecord
from Mailer.models import mailer_email_is_valide, mailer_obfuscate_email
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Account.models import AccountCreateError, account_create
from Account.views import account_vraag_email_bevestiging
from Score.models import Score, ScoreHist
from NhbStructuur.models import NhbLid
from .leeftijdsklassen import get_sessionvars_leeftijdsklassen
from .models import SchutterBoog, SchutterNhbLidGeenEmail, SchutterNhbLidInactief
from .forms import RegistreerForm
import logging
import copy


TEMPLATE_PROFIEL = 'schutter/profiel.dtl'
TEMPLATE_REGISTREER = 'schutter/registreer-nhb-account.dtl'
TEMPLATE_VOORKEUREN = 'schutter/voorkeuren.dtl'
TEMPLATE_VOORKEUREN_OPGESLAGEN = 'schutter/voorkeuren-opgeslagen.dtl'
TEMPLATE_LEEFTIJDSKLASSEN = 'schutter/leeftijdsklassen.dtl'

my_logger = logging.getLogger('NHBApps.Schutter')


class ProfielView(UserPassesTestMixin, TemplateView):

    """ Dit is de profiel pagina van een schutter """

    template_name = TEMPLATE_PROFIEL

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _find_scores(nhblid):
        """ Zoek alle scores van deze schutter """
        boogtype2str = dict()
        for boog in BoogType.objects.all():
            boogtype2str[boog.afkorting] = boog.beschrijving
        # for

        objs = list()
        for obj in HistCompetitieIndividueel.objects.filter(schutter_nr=nhblid.nhb_nr):
            wedstrijd = HistCompetitie.comptype2str[obj.histcompetitie.comp_type]
            datum_str = 'Seizoen ' + obj.histcompetitie.seizoen
            try:
                boog_str = boogtype2str[obj.boogtype]
            except KeyError:
                boog_str = "?"
            for score in (obj.score1, obj.score2, obj.score3, obj.score4, obj.score5, obj.score6, obj.score7):
                if score:
                    entry = dict()
                    entry['score'] = score
                    entry['datum'] = datum_str
                    entry['wedstrijd'] = wedstrijd
                    entry['boog'] = boog_str
                    objs.append(entry)
            # for
        # for

        # records niet toevoegen, want dan wordt het dubbel getoond
        return objs

    @staticmethod
    def _find_records(nhblid):
        """ Zoek de records van deze schutter """
        objs = list()
        for rec in IndivRecord.objects.filter(nhb_lid=nhblid).order_by('-datum'):
            rec.url = reverse('Records:specifiek', kwargs={'discipline': rec.discipline, 'nummer': rec.volg_nr})
            objs.append(rec)
        # for
        return objs

    @staticmethod
    def _find_regiocompetities(nhblid):
        """ Zoek regiocompetities waar de schutter zich op aan kan melden """

        # toon alle deelcompetities waarop ingeschreven kan worden met de bogen van de schutter
        # oftewel (deelcompetitie, schutterboog, is_ingeschreven)

        # stel vast welke boogtypen de schutter mee wil schieten (opt-in)
        # en welke hij informatie over wil hebben (opt-out)
        boog_afkorting_wedstrijd = list()
        boog_afkorting_info = list()

        boog_dict = dict()      # [afkorting] = BoogType()
        for boogtype in BoogType.objects.all():
            boog_dict[boogtype.afkorting] = boogtype
            boog_afkorting_info.append(boogtype.afkorting)
        # for

        schutterboog_dict = dict()  # [boog_afkorting] = SchutterBoog()
        # typische 0 tot 5 records
        for schutterboog in nhblid.schutterboog_set.select_related('boogtype').all():
            afkorting = schutterboog.boogtype.afkorting
            schutterboog_dict[afkorting] = schutterboog
            if schutterboog.voor_wedstrijd:
                boog_afkorting_wedstrijd.append(afkorting)
                boog_afkorting_info.remove(afkorting)
            elif not schutterboog.heeft_interesse:
                boog_afkorting_info.remove(afkorting)
        # for

        boog_afkorting_all = set(boog_afkorting_info + boog_afkorting_wedstrijd)

        # print("wedstrijdbogen: %s" % repr(boog_afkorting_wedstrijd))
        # print("info: %s" % repr(boog_afkorting_info))
        # print("all: %s" % repr(boog_afkorting_all))

        # zoek alle inschrijvingen erbij
        inschrijvingen = list()
        schutterbogen = [schutterboog for _, schutterboog in schutterboog_dict.items()]
        for obj in RegioCompetitieSchutterBoog.objects.filter(schutterboog__in=schutterbogen):
            inschrijvingen.append(obj)
        # for

        objs_info = list()
        objs_wedstrijd = list()

        # zoek deelcompetities in deze regio (typisch zijn er 2 in de regio: 18m en 25m)
        regio = nhblid.bij_vereniging.regio
        for deelcompetitie in DeelCompetitie.objects.\
                                select_related('competitie').\
                                filter(laag=LAAG_REGIO, nhb_regio=regio, is_afgesloten=False):
            # zoek de klassen erbij die de schutter interessant vindt
            afkortingen = list(boog_afkorting_all)
            for klasse in CompetitieKlasse.objects.\
                                select_related('indiv__boogtype').\
                                filter(indiv__boogtype__afkorting__in=boog_afkorting_all,
                                       competitie=deelcompetitie.competitie):
                afk = klasse.indiv.boogtype.afkorting
                if afk in afkortingen:
                    # dit boogtype nog niet gehad
                    afkortingen.remove(afk)
                    obj = copy.copy(deelcompetitie)
                    obj.boog_afkorting = afk
                    obj.boog_beschrijving = boog_dict[afk].beschrijving
                    obj.is_ingeschreven = False
                    if afk in boog_afkorting_wedstrijd:
                        obj.is_voor_wedstrijd = True
                        objs_wedstrijd.append(obj)
                    else:
                        obj.is_voor_wedstrijd = False
                        objs_info.append(obj)
            # for
        # for

        # zoek uit of de schutter al ingeschreven is
        for obj in objs_wedstrijd:
            schutterboog = schutterboog_dict[obj.boog_afkorting]
            try:
                inschrijving = RegioCompetitieSchutterBoog.objects.get(deelcompetitie=obj, schutterboog=schutterboog)
            except RegioCompetitieSchutterBoog.DoesNotExist:
                # niet ingeschreven
                obj.url_inschrijven = reverse('Schutter:inschrijven', kwargs={'schutterboog_pk': schutterboog.pk, 'deelcomp_pk': obj.pk})
            else:
                obj.is_ingeschreven = True
                obj.url_uitschrijven = reverse('Schutter:uitschrijven', kwargs={'regiocomp_pk': inschrijving.pk})
                inschrijvingen.remove(inschrijving)
        # for

        # voeg alle inschrijvingen toe waar geen boog meer voor gekozen is,
        # zodat uitgeschreven kan worden
        for obj in inschrijvingen:
            afk = obj.schutterboog.boogtype.afkorting
            deelcomp = obj.deelcompetitie
            deelcomp.is_ingeschreven = True
            deelcomp.is_voor_wedstrijd = True
            deelcomp.boog_niet_meer = True
            deelcomp.boog_beschrijving = boog_dict[afk].beschrijving
            deelcomp.url_uitschrijven = reverse('Schutter:uitschrijven', kwargs={'regiocomp_pk': obj.pk})
            objs_wedstrijd.append(deelcomp)
        # for

        objs = objs_wedstrijd
        if len(objs_info):
            objs_info[0].separator_before = True
            objs.extend(objs_info)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        account = self.request.user

        _, _, is_jong, _, _ = get_sessionvars_leeftijdsklassen(self.request)
        context['toon_leeftijdsklassen'] = is_jong

        nhblid = account.nhblid_set.all()[0]
        context['nhblid'] = nhblid
        context['records'] = self._find_records(nhblid)
        context['scores'] = self._find_scores(nhblid)
        context['regiocompetities'] = self._find_regiocompetities(nhblid)

        menu_dynamics(self.request, context, actief='schutter')
        return context


class VoorkeurenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen schutters hun voorkeuren inzien en aanpassen """

    template_name = TEMPLATE_VOORKEUREN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn en schutter rol gekozen hebben
        return rol_get_huidige(self.request) in (Rollen.ROL_SCHUTTER, Rollen.ROL_CWZ)

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    @staticmethod
    def _get_nhblid_or_404(request, nhblid_pk):
        """ Geeft het nhblid record terug van de schutter zelf,
            of in geval van de CWZ de gekozen schutter """

        rol_nu, functie_nu = rol_get_huidige_functie(request)
        if rol_nu == Rollen.ROL_CWZ:
            try:
                # conversie naar integer geef input-controle
                nhblid_pk = int(nhblid_pk)
            except (ValueError, TypeError):
                # nhblid_pk was geen getal
                raise Resolver404()

            try:
                nhblid = NhbLid.objects.get(pk=nhblid_pk)
            except NhbLid.DoesNotExist:
                raise Resolver404()

            # laatste control: het nhblid moet lid zijn bij de vereniging van de CWZ
            if nhblid.bij_vereniging != functie_nu.nhb_ver:
                raise Resolver404()

            return nhblid

        account = request.user
        return account.nhblid_set.all()[0]      # ROL_SCHUTTER geeft bescherming tegen geen nhblid

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als een POST request ontvangen is."""
        nhblid = self._get_nhblid_or_404(request, request.POST.get('nhblid_pk', None))

        # sla de nieuwe voorkeuren op in SchutterBoog records (1 per boogtype)
        # werkt alleen na een GET (maakt de SchutterBoog records aan)
        for obj in SchutterBoog.objects.filter(nhblid=nhblid):
            check_info = 'info_' + obj.boogtype.afkorting

            old_voor_wedstrijd = obj.voor_wedstrijd
            obj.voor_wedstrijd = False
            if request.POST.get('schiet_' + obj.boogtype.afkorting, None):
                obj.voor_wedstrijd = True

            old_heeft_interesse = obj.heeft_interesse
            obj.heeft_interesse = False
            if request.POST.get('info_' + obj.boogtype.afkorting, None):
                obj.heeft_interesse = True

            old_voorkeur_dutchtarget_18m = obj.voorkeur_dutchtarget_18m
            obj.voorkeur_dutchtarget_18m = False
            if obj.boogtype.afkorting == "R":
                if request.POST.get('voorkeur_DT_18m', None):
                    obj.voorkeur_dutchtarget_18m = True

            if (old_voor_wedstrijd != obj.voor_wedstrijd or
                    old_heeft_interesse != obj.heeft_interesse or
                    old_voorkeur_dutchtarget_18m != obj.voorkeur_dutchtarget_18m):
                # wijzigingen opslaan
                obj.save()
        # for

        if rol_get_huidige(request) == Rollen.ROL_CWZ:
            # stuur de CWZ terug naar zijn ledenlijst
            return HttpResponseRedirect(reverse('Vereniging:leden-voorkeuren'))

        context = dict()
        menu_dynamics(request, context, actief='schutter')
        return render(request, TEMPLATE_VOORKEUREN_OPGESLAGEN, context)

    @staticmethod
    def _get_bogen(nhblid):
        """ Retourneer een lijst met SchutterBoog objecten, aangevuld met hulpvelden """

        # haal de SchutterBoog records op van deze gebruiker
        objs = SchutterBoog.objects.filter(nhblid=nhblid).order_by('boogtype__volgorde')

        # maak ontbrekende SchutterBoog records aan, indien nodig
        boogtypen = BoogType.objects.all()
        if len(objs) < len(boogtypen):
            aanwezig = objs.values_list('boogtype__pk', flat=True)
            for boogtype in boogtypen.exclude(pk__in=aanwezig):
                schutterboog = SchutterBoog()
                schutterboog.nhblid = nhblid
                schutterboog.boogtype = boogtype
                schutterboog.save()
            # for
            objs = SchutterBoog.objects.filter(nhblid=nhblid).order_by('boogtype__volgorde')

        # voeg de checkbox velden toe en AG informatie
        voorkeur_dt = False
        for obj in objs:
            obj.check_schiet = 'schiet_' + obj.boogtype.afkorting
            obj.check_info = 'info_' + obj.boogtype.afkorting
            if obj.voorkeur_dutchtarget_18m:
                voorkeur_dt = True

            # haal AG van 18m en 25m op, indien aanwezig
            scores = Score.objects.filter(schutterboog=obj, is_ag=True, afstand_meter=18)
            if len(scores):
                score = scores[0]
                obj.ag_18_waarde = score.waarde / 1000
                hist = ScoreHist.objects.filter(score=score).order_by('-datum')
                if len(hist):
                    obj.ag_18_scorehist = hist[0]

            scores = Score.objects.filter(schutterboog=obj, is_ag=True, afstand_meter=25)
            if len(scores):
                score = scores[0]
                obj.ag_25_waarde = score.waarde / 1000
                hist = ScoreHist.objects.filter(score=score).order_by('-datum')
                if len(hist):
                    obj.ag_25_scorehist = hist[0]
        # for
        return objs, voorkeur_dt

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            nhblid_pk = kwargs['nhblid_pk']
        except KeyError:
            nhblid_pk = None
        nhblid = self._get_nhblid_or_404(self.request, nhblid_pk)

        bogen, voorkeur_dt = self._get_bogen(nhblid)
        context['bogen'] = bogen
        context['voorkeur_dt'] = voorkeur_dt

        if rol_get_huidige(self.request) == Rollen.ROL_CWZ:
            context['nhblid_pk'] = nhblid.pk
            context['nhblid'] = nhblid
            context['is_cwz'] = True

        context['opslaan_url'] = reverse('Schutter:voorkeuren')

        menu_dynamics(self.request, context, actief='schutter')
        return context


class LeeftijdsklassenView(UserPassesTestMixin, TemplateView):
    """ Django class-based view voor de leeftijdsklassen """

    # class variables shared by all instances
    template_name = TEMPLATE_LEEFTIJDSKLASSEN

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol == Rollen.ROL_SCHUTTER

    def handle_no_permission(self):
        """ gebruiker heeft geen toegang --> redirect naar het plein """
        return HttpResponseRedirect(reverse('Plein:plein'))

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        huidige_jaar, leeftijd, is_jong, wlst, clst = get_sessionvars_leeftijdsklassen(self.request)
        context['plein_is_jonge_schutter'] = is_jong
        context['plein_huidige_jaar'] = huidige_jaar
        context['plein_leeftijd'] = leeftijd
        context['plein_wlst'] = wlst
        context['plein_clst'] = clst

        menu_dynamics(self.request, context)
        return context


def schutter_create_account_nhb(nhb_nummer, email, nieuw_wachtwoord):
    """ Maak een nieuw account aan voor een NHB lid
        raises AccountError als:
            - er al een account bestaat
            - het nhb nummer niet valide is
            - het email adres niet bekend is bij de nhb
            - het email adres niet overeen komt
        geeft de url terug die in de email verstuurd moet worden
    """
    # zoek het email adres van dit NHB lid erbij
    try:
        # deze conversie beschermd ook tegen gevaarlijke invoer
        nhb_nr = int(nhb_nummer)
    except ValueError:
        raise AccountCreateError('Onbekend NHB nummer')

    try:
        nhblid = NhbLid.objects.get(nhb_nr=nhb_nr)
    except NhbLid.DoesNotExist:
        raise AccountCreateError('Onbekend NHB nummer')

    if not mailer_email_is_valide(nhblid.email):
        raise SchutterNhbLidGeenEmail()

    if email != nhblid.email:
        raise AccountCreateError('De combinatie van NHB nummer en email worden niet herkend. Probeer het nog eens.')

    if not nhblid.is_actief_lid:
        raise SchutterNhbLidInactief()

    # maak het account aan
    account, accountmail = account_create(nhb_nummer, nhblid.voornaam, nhblid.achternaam, nieuw_wachtwoord, email, False)

    # koppelen nhblid en account
    nhblid.account = account
    nhblid.save()

    account_vraag_email_bevestiging(accountmail, nhb_nummer=nhb_nummer, email=email)


class RegistreerNhbNummerView(TemplateView):
    """
        Deze view wordt gebruikt om het NHB nummer in te voeren voor een nieuw account.
    """

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        form = RegistreerForm(request.POST)
        if form.is_valid():
            nhb_nummer = form.cleaned_data.get('nhb_nummer')
            email = form.cleaned_data.get('email')
            nieuw_wachtwoord = form.cleaned_data.get('nieuw_wachtwoord')
            from_ip = get_safe_from_ip(request)
            try:
                schutter_create_account_nhb(nhb_nummer, email, nieuw_wachtwoord)
            except SchutterNhbLidGeenEmail:
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s heeft geen email adres.' % nhb_nummer)

                form.add_error(None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')
                my_logger.info('%s REGISTREER Geblokkeerd voor NHB nummer %s (geen email)' % (from_ip, repr(nhb_nummer)))
                # TODO: redirect naar een pagina met een uitgebreider duidelijk bericht
            except AccountCreateError as exc:
                form.add_error(None, str(exc))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Mislukt voor nhb nummer %s vanaf IP %s: %s" % (repr(nhb_nummer), from_ip, str(exc)))
                my_logger.info('%s REGISTREER Mislukt voor NHB nummer %s (reden: %s)' % (from_ip, repr(nhb_nummer), str(exc)))
            except SchutterNhbLidInactief:
                # NHB lid is mag niet gebruik maken van de diensten van de NHB, inclusief deze website
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s is inactief (geblokkeerd van gebruik NHB diensten).' % nhb_nummer)
                form.add_error(None, 'Gebruik van NHB diensten is geblokkeerd. Neem contact op met de secretaris van je vereniging.')
                my_logger.info('%s REGISTREER Geblokkeerd voor NHB nummer %s (inactief)' % (from_ip, repr(nhb_nummer)))
                # TODO: redirect naar een pagina met een uitgebreider duidelijk bericht
            else:
                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Account aangemaakt voor NHB nummer %s vanaf IP %s" % (repr(nhb_nummer), from_ip))
                my_logger.info('%s REGISTREER account aangemaakt voor NHB nummer %s' % (from_ip, repr(nhb_nummer)))

                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = mailer_obfuscate_email(email)
                return HttpResponseRedirect(reverse('Account:aangemaakt'))

        # still here --> re-render with error message
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_REGISTREER, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # GET operation --> create empty form
        form = RegistreerForm()
        context = {'form': form}
        menu_dynamics(request, context, actief="inloggen")
        return render(request, TEMPLATE_REGISTREER, context)


class RegiocompetitieInschrijvenView(View):

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de schutter op zijn profiel pagina
            de knop Inschrijven gebruikt voor een specifieke regiocompetitie en boogtype.
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
            raise Resolver404()

        # converteer en doe eerste controle op de parameters
        try:
            deelcomp_pk = int(kwargs['deelcomp_pk'][:10])
            schutterboog_pk = int(kwargs['schutterboog_pk'][:10])

            schutterboog = SchutterBoog.objects.get(pk=schutterboog_pk)
            deelcomp = DeelCompetitie.objects.get(pk=deelcomp_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Resolver404()
        except (SchutterBoog.DoesNotExist, DeelCompetitie.DoesNotExist):
            # niet bestaand record
            raise Resolver404()

        # controleer dat schutterboog bij de ingelogde gebruiker hoort
        # controleer dat deelcompetitie bij de juist regio hoort
        if schutterboog.nhblid != nhblid or deelcomp.laag != LAAG_REGIO or deelcomp.nhb_regio != nhblid.bij_vereniging.regio:
            raise Resolver404()

        # invoer geaccepteerd

        # zoek het aanvangsgemiddelde erbij
        afstand = deelcomp.competitie.afstand
        try:
            score = Score.objects.get(is_ag=True, schutterboog=schutterboog, afstand_meter=deelcomp.competitie.afstand)
        except Score.DoesNotExist:
            ag = None
        else:
            ag = score.waarde / 1000

        regiocompetitie_schutterboog_aanmelden(deelcomp.competitie, schutterboog, ag)

        return HttpResponseRedirect(reverse('Schutter:profiel'))


class RegiocompetitieUitschrijvenView(View):

    def post(self, request, *args, **kwargs):
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
            raise Resolver404()

        # converteer en doe eerste controle op de parameters
        try:
            regiocomp_pk = int(kwargs['regiocomp_pk'][:10])
            inschrijving = RegioCompetitieSchutterBoog.objects.get(pk=regiocomp_pk)
        except (ValueError, KeyError):
            # vuilnis
            raise Resolver404()
        except RegioCompetitieSchutterBoog.DoesNotExist:
            # niet bestaand record
            raise Resolver404()

        # controleer dat deze inschrijving bij het nhblid hoort
        if inschrijving.schutterboog.nhblid != nhblid:
            raise Resolver404()

        # schrijf de schutter uit
        inschrijving.delete()

        return HttpResponseRedirect(reverse('Schutter:profiel'))

# end of file
