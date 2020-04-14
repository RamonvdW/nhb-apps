# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect
from django.urls import reverse, Resolver404
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Plein.menu import menu_dynamics
from Functie.rol import Rollen, rol_get_huidige, rol_get_huidige_functie
from HistComp.models import HistCompetitie, HistCompetitieIndividueel
from BasisTypen.models import BoogType
from NhbStructuur.models import NhbLid
from Records.models import IndivRecord
from Mailer.models import queue_email
from Logboek.models import schrijf_in_logboek
from Overig.helpers import get_safe_from_ip
from Account.models import AccountCreateError
from Account.views import obfuscate_email
from Score.models import Score, ScoreHist
from .leeftijdsklassen import get_sessionvars_leeftijdsklassen
from .models import SchutterBoog, account_create_nhb, AccountCreateNhbGeenEmail
from .forms import RegistreerForm
import logging

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
        objs = list()
        for rec in IndivRecord.objects.filter(nhb_lid=nhblid).order_by('-datum'):
            rec.url = reverse('Records:specifiek', kwargs={'discipline': rec.discipline, 'nummer': rec.volg_nr})
            objs.append(rec)
        # for
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
            scores = Score.objects.filter(schutterboog=obj, afstand_meter=18)
            if len(scores):
                score = scores[0]
                obj.ag_18_waarde = score.waarde / 1000
                hist = ScoreHist.objects.filter(score=score).order_by('-datum')
                if len(hist):
                    obj.ag_18_scorehist = hist[0]

            scores = Score.objects.filter(schutterboog=obj, afstand_meter=25)
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
            error = False
            try:
                ack_url = account_create_nhb(nhb_nummer, email, nieuw_wachtwoord)
            except AccountCreateNhbGeenEmail:
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit='NHB lid %s heeft geen email adres.' % nhb_nummer)

                form.add_error(None, 'Geen email adres bekend. Neem contact op met de secretaris van je vereniging.')
                # TODO: redirect naar een pagina met een uitgebreider duidelijk bericht
            except AccountCreateError as exc:
                form.add_error(None, str(exc))

                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Mislukt voor nhb nummer %s vanaf IP %s: %s" % (repr(nhb_nummer), from_ip, str(exc)))
                my_logger.info('%s REGISTREER Mislukt voor NHB nummer %s (reden: %s)' % (from_ip, repr(nhb_nummer), str(exc)))
            else:
                # schrijf in het logboek
                schrijf_in_logboek(account=None,
                                   gebruikte_functie="Registreer met NHB nummer",
                                   activiteit="Account aangemaakt voor NHB nummer %s vanaf IP %s" % (repr(nhb_nummer), from_ip))
                my_logger.info('%s REGISTREER account aangemaakt voor NHB nummer %s' % (from_ip, repr(nhb_nummer)))

                text_body = "Hallo!\n\n" +\
                            "Je hebt een account aangemaakt op de website van de NHB.\n" +\
                            "Klik op onderstaande link om dit te bevestigen.\n\n" +\
                            ack_url + "\n\n" +\
                            "Als jij dit niet was, neem dan contact met ons op via info@handboogsport.nl\n\n" +\
                            "Veel plezier met de site!\n" +\
                            "Het bondsburo\n"

                queue_email(email, 'Aanmaken account voltooien', text_body)

                request.session['login_naam'] = nhb_nummer
                request.session['partial_email'] = obfuscate_email(email)
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



# end of file
