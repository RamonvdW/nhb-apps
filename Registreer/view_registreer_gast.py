# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render, reverse, redirect, Http404
from django.contrib.auth import update_session_auth_hash
from django.views.generic import View, TemplateView
from Account.models import get_account
from Account.operations import (AccountCreateError, account_create, account_test_wachtwoord_sterkte,
                                auto_login_gast_account)
from BasisTypen.definities import GESLACHT2STR
from Logboek.models import schrijf_in_logboek
from Mailer.operations import mailer_queue_email, render_email_template
from Overig.helpers import get_safe_from_ip, maak_unaccented
from Registreer.definities import (REGISTRATIE_FASE_EMAIL, REGISTRATIE_FASE_PASS, REGISTRATIE_FASE_CLUB,
                                   REGISTRATIE_FASE_LAND, REGISTRATIE_FASE_AGE, REGISTRATIE_FASE_TEL,
                                   REGISTRATIE_FASE_WA_ID, REGISTRATIE_FASE_GENDER, REGISTRATIE_FASE_CONFIRM,
                                   REGISTRATIE_FASE_BEKEND_LID, REGISTRATIE_FASE_COMPLEET)
from Registreer.forms import RegistreerGastForm, scrub_input_name
from Registreer.models import GastRegistratie, GastRegistratieRateTracker
from Registreer.operations import registratie_gast_volgende_lid_nr, registratie_gast_is_open
from Sporter.models import Sporter
from TijdelijkeCodes.operations import (set_tijdelijke_codes_receiver, RECEIVER_BEVESTIG_EMAIL_REG_GAST,
                                        maak_tijdelijke_code_bevestig_email_registreer_gast)
from Vereniging.models import Vereniging
import datetime
import logging


TEMPLATE_REGISTREER_GAST = 'registreer/registreer-gast.dtl'
TEMPLATE_REGISTREER_GAST_VERVOLG = 'registreer/registreer-gast-03-vervolg.dtl'
TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL = 'registreer/registreer-gast-01-bevestig-email.dtl'
TEMPLATE_REGISTREER_GAST_EMAIL_BEVESTIGD = 'registreer/registreer-gast-02-email-bevestigd.dtl'
TEMPLATE_REGISTREER_GAST_WACHTWOORD = 'registreer/registreer-gast-04-kies-wachtwoord.dtl'
TEMPLATE_REGISTREER_GAST_CLUB = 'registreer/registreer-gast-05-club.dtl'
TEMPLATE_REGISTREER_GAST_LAND_BOND_NR = 'registreer/registreer-gast-06-land-bond-nr.dtl'
TEMPLATE_REGISTREER_GAST_AGE = 'registreer/registreer-gast-07-age.dtl'
TEMPLATE_REGISTREER_GAST_TEL = 'registreer/registreer-gast-08-tel.dtl'
TEMPLATE_REGISTREER_GAST_WA_ID = 'registreer/registreer-gast-09-wa-id.dtl'
TEMPLATE_REGISTREER_GAST_GENDER = 'registreer/registreer-gast-10-gender.dtl'
TEMPLATE_REGISTREER_GAST_CONFIRM = 'registreer/registreer-gast-25-confirm.dtl'
TEMPLATE_REGISTREER_GAST_BEKEND_ALS_LID = 'registreer/registreer-gast-98-bekend-als-lid.dtl'

EMAIL_TEMPLATE_GAST_BEVESTIG_EMAIL = 'email_registreer/gast-bevestig-toegang-email.dtl'
EMAIL_TEMPLATE_GAST_LID_NR = 'email_registreer/gast-tijdelijk-bondsnummer.dtl'

my_logger = logging.getLogger('MH.Registreer')


class RegistreerGastView(TemplateView):
    """
        Deze view wordt gebruikt om het bondsnummer en e-mailadres van een lid en daarmee een account aan te maken.
    """

    @staticmethod
    def _check_rate_limit(from_ip) -> bool:
        """
            Blokkeer meerdere verzoeken binnen 1 minuut.

            Returns 'mag door':
                True:  Mag door
                False: Verzoek blokkeren
        """
        mag_door = False

        now = timezone.now()
        uur = now.hour
        minuut = uur * 60 + now.minute      # sinds middernacht

        # ga er vanuit dat er meerdere threads zijn die tegelijkertijd bezig willen!
        with transaction.atomic():
            tracker, _ = GastRegistratieRateTracker.objects.get_or_create(from_ip=from_ip)

            if tracker.teller_minuut <= 3 and tracker.teller_uur <= 10:
                mag_door = True

                if tracker.minuut != minuut:
                    tracker.teller_minuut = 0
                    tracker.minuut = minuut

                if tracker.uur != uur:
                    tracker.teller_uur = 0
                    tracker.uur = uur

                tracker.teller_minuut += 1
                tracker.teller_uur += 1

                tracker.save()
            else:
                # geblokkeerd --> voorkom onnodig loggen
                pass

        return mag_door

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        # begin met een leeg formulier
        form = RegistreerGastForm()

        context = {
            'form': form,
            'url_aanmaken': reverse('Registreer:gast'),
            'gast_is_open': registratie_gast_is_open(),
            'kruimels': (
                (reverse('Registreer:begin'), 'Account aanmaken'),
                (None, 'Gast')),
        }

        return render(request, TEMPLATE_REGISTREER_GAST, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """

        form = RegistreerGastForm(request.POST)

        gast_is_open = registratie_gast_is_open()

        # still here --> re-render with error message
        context = {
            'form': form,
            'email_bb': settings.EMAIL_BONDSBUREAU,
            'gast_is_open': gast_is_open,
            'verberg_login_knop': True,
            'url_aanmaken': reverse('Registreer:gast'),
            'kruimels': (
                (reverse('Registreer:begin'), 'Account aanmaken'),
                (None, 'Gast')),
        }

        if not gast_is_open:
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        if not form.is_valid():
            # opnieuw
            context['toon_tip'] = True
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        from_ip = get_safe_from_ip(request)

        # begrens de frequentie
        mag_door = self._check_rate_limit(from_ip)
        if not mag_door:
            # verzoek moet geblokkeerd worden
            form.add_error(None, 'te snel. Wacht 1 minuut.')
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        # compleetheid is gecontroleerd door het formulier
        voornaam = form.cleaned_data.get('voornaam')
        achternaam = form.cleaned_data.get('achternaam')
        email = form.cleaned_data.get('email')

        # kijk of er al een verzoek loopt van dezelfde gebruiker
        gast, is_created = GastRegistratie.objects.get_or_create(voornaam=voornaam,
                                                                 achternaam=achternaam,
                                                                 email=email)
        if not is_created:
            # verzoek moet geblokkeerd worden
            form.add_error(None, 'dubbel verzoek.')
            return render(request, TEMPLATE_REGISTREER_GAST, context)

        # het is een nieuw verzoek
        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        gast.fase = REGISTRATIE_FASE_EMAIL
        gast.logboek = '[%s] IP=%s: aangemaakt met naam en e-mail\n' % (stamp_str, from_ip)
        gast.save()

        # begin een nieuwe gast-account registratie

        # laat het e-mailadres bevestigen (ook al accepteren we deze straks niet)

        # schrijf in syslog om database vervuiling te voorkomen
        my_logger.info('%s REGISTREER gast-account aanmaken; stuur e-mail' % from_ip)

        # maak de url aan om het e-mailadres te bevestigen
        url = maak_tijdelijke_code_bevestig_email_registreer_gast(gast,
                                                                  naam=voornaam + achternaam,
                                                                  stamp=stamp_str,
                                                                  from_ip=from_ip,
                                                                  gast_email=email)

        # maak de e-mail aan
        context = {
            'url': url,
            'voornaam': gast.voornaam,
            'naam_site': settings.NAAM_SITE,
            'contact_email': settings.EMAIL_BONDSBUREAU,
        }
        mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_BEVESTIG_EMAIL)

        # stuur de e-mail
        mailer_queue_email(gast.email,
                           'Aanmaken gast-account voltooien',
                           mail_body,
                           enforce_whitelist=False)     # deze mails altijd doorlaten

        context['email'] = email
        return render(request, TEMPLATE_REGISTREER_GAST_BEVESTIG_EMAIL, context)


def receive_bevestiging_gast_email(request, gast):
    """ deze functie wordt vanuit een POST context aangeroepen als een tijdelijke url gevolgd wordt
        om het email adres van een nieuw gast-account te bevestigen.
            gast is een GastRegistratie object.
        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """
    from_ip = get_safe_from_ip(request)

    # schrijf in syslog om database vervuiling te voorkomen
    my_logger.info('%s REGISTREER gast-account e-mail is bevestigd' % from_ip)

    # schrijf in het logboek
    msg = "E-mail voor gast-account e-mail %s bevestigd vanaf IP %s" % (gast.email, from_ip)
    schrijf_in_logboek(account=None,
                       gebruikte_functie="Registreer gast-account",
                       activiteit=msg)

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

    gast.email_is_bevestigd = True
    gast.logboek += '[%s] IP=%s: e-mail is bevestigd\n' % (stamp_str, from_ip)
    gast.save(update_fields=['email_is_bevestigd', 'logboek'])

    # controleer dat e-mailadres niet bekend is in het CRM
    lid_nrs = list(Sporter.objects.filter(email=gast.email, is_actief_lid=True).values_list('lid_nr', flat=True))
    if len(lid_nrs) > 0:
        context = {
            'email': gast.email,
            'email_support': settings.EMAIL_BONDSBUREAU,
            'url_registreer_khsn': reverse('Registreer:lid'),
        }
        gast.fase = REGISTRATIE_FASE_BEKEND_LID
        if len(lid_nrs) == 1:
            context['lid_nr_str'] = lid_nr_str = '%s' % lid_nrs[0]
            gast.logboek += '[%s] E-mail overlap gevonden met lid met lid_nr %s\n' % (stamp_str, lid_nr_str)
        else:
            context['lid_nrs_str'] = lid_nrs_str = ', '.join([str(lid_nr)
                                                              for lid_nr in lid_nrs])
            gast.logboek += '[%s] E-mail overlap gevonden met leden met lid_nrs %s\n' % (stamp_str, lid_nrs_str)
        gast.save(update_fields=['fase', 'logboek'])
        return render(request, TEMPLATE_REGISTREER_GAST_BEKEND_ALS_LID, context)

    gast.lid_nr = registratie_gast_volgende_lid_nr()
    gast.logboek += "[%s] Lidnummer %s is toegekend\n" % (stamp_str, gast.lid_nr)
    gast.save(update_fields=['lid_nr', 'logboek'])

    try:
        username = str(gast.lid_nr)
        wachtwoord = 'Gast' + from_ip + stamp_str       # tijdelijk en lastig te raden (geen risico)
        account = account_create(username, gast.voornaam, gast.achternaam, wachtwoord, gast.email, True)
    except AccountCreateError as exc:
        gast.logboek += '[%s] account_create mislukt: %s\n' % (stamp_str, exc)
        gast.save(update_fields=['logboek'])
        raise Http404('Account aanmaken is onverwacht mislukt')

    account.vraag_nieuw_wachtwoord = True
    account.is_gast = True
    account.save(update_fields=['vraag_nieuw_wachtwoord', 'is_gast'])

    gast.account = account
    gast.logboek += '[%s] Account is aangemaakt\n' % stamp_str
    gast.fase = REGISTRATIE_FASE_PASS
    gast.save(update_fields=['account', 'logboek', 'fase'])

    # stuur een e-mail met het bondsnummer
    # maak de e-mail aan
    context = {
        'url': reverse('Account:wachtwoord-vergeten'),
        'voornaam': gast.voornaam,
        'lid_nr': gast.lid_nr,
        'naam_site': settings.NAAM_SITE,
        'contact_email': settings.EMAIL_BONDSBUREAU,
    }
    mail_body = render_email_template(context, EMAIL_TEMPLATE_GAST_LID_NR)

    # stuur de e-mail
    mailer_queue_email(gast.email,
                       'Bondsnummer %s toegekend' % gast.lid_nr,
                       mail_body,
                       enforce_whitelist=False)  # deze mails altijd doorlaten

    now = timezone.now()
    stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    gast.logboek += '[%s] e-mail verstuurd met bondsnummer\n' % stamp_str
    gast.save(update_fields=['logboek'])

    schrijf_in_logboek(account=None,
                       gebruikte_functie="Registreer gast-account",
                       activiteit="E-mail is bevestigd; account %s aangemaakt" % gast.lid_nr)

    # log de gebruiker automatisch in op zijn nieuwe account
    # gebruiker weet het wachtwoord niet
    auto_login_gast_account(request, account)

    context = {
        'verberg_login_knop': True,
        'toon_broodkruimels': False,
        'lid_nr': gast.lid_nr,
        'url_volgende_vraag': reverse('Registreer:gast-volgende-vraag'),
    }

    return render(request, TEMPLATE_REGISTREER_GAST_EMAIL_BEVESTIGD, context)


set_tijdelijke_codes_receiver(RECEIVER_BEVESTIG_EMAIL_REG_GAST, receive_bevestiging_gast_email)


class RegistreerGastVervolgView(TemplateView):
    """
        Deze view geeft de landing page om de gebruiker het proces uit te leggen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_REGISTREER_GAST_VERVOLG

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """

        if not request.user.is_authenticated:
            return redirect('Plein:plein')

        account = get_account(request)
        gast = account.gastregistratie_set.first()
        if not gast:
            # dit is geen gast-account
            return redirect('Plein:plein')

        if gast.fase == REGISTRATIE_FASE_COMPLEET:
            # registratie is al voltooid
            return redirect('Plein:plein')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        # geen kruimels
        return context


class RegistreerGastVolgendeVraagView(View):

    # class variables shared by all instances
    # (none)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account = None
        self.gast = None

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """

        if not request.user.is_authenticated:
            return redirect('Plein:plein')

        self.account = get_account(request)
        gast = self.account.gastregistratie_set.first()
        if not gast:
            # dit is geen gast-account
            return redirect('Plein:plein')

        if gast.fase == REGISTRATIE_FASE_COMPLEET:
            # registratie is al voltooid
            return redirect('Plein:plein')

        self.gast = gast

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = dict()

        gast = self.gast

        if gast.fase == REGISTRATIE_FASE_PASS:
            template_name = TEMPLATE_REGISTREER_GAST_WACHTWOORD
            context['account'] = self.account

        elif gast.fase == REGISTRATIE_FASE_CLUB:
            template_name = TEMPLATE_REGISTREER_GAST_CLUB
            context['club'] = gast.club
            context['plaats'] = gast.club_plaats

        elif gast.fase == REGISTRATIE_FASE_LAND:
            template_name = TEMPLATE_REGISTREER_GAST_LAND_BOND_NR
            context['land'] = gast.land
            context['bond'] = gast.eigen_sportbond_naam
            context['lid_nr'] = gast.eigen_lid_nummer

        elif gast.fase == REGISTRATIE_FASE_AGE:
            template_name = TEMPLATE_REGISTREER_GAST_AGE
            if gast.geboorte_datum.year == 2000 and gast.geboorte_datum.month == 1 and gast.geboorte_datum.day == 1:
                context['jaar'] = ''
                context['maand'] = ''
                context['dag'] = ''
            else:
                context['jaar'] = gast.geboorte_datum.year
                context['maand'] = gast.geboorte_datum.month
                context['dag'] = gast.geboorte_datum.day

        elif gast.fase == REGISTRATIE_FASE_TEL:
            template_name = TEMPLATE_REGISTREER_GAST_TEL
            context['tel'] = gast.telefoon

        elif gast.fase == REGISTRATIE_FASE_WA_ID:
            template_name = TEMPLATE_REGISTREER_GAST_WA_ID
            context['wa_id'] = gast.wa_id

        elif gast.fase == REGISTRATIE_FASE_GENDER:
            template_name = TEMPLATE_REGISTREER_GAST_GENDER
            context['geslacht'] = gast.geslacht

        elif gast.fase == REGISTRATIE_FASE_CONFIRM:
            template_name = TEMPLATE_REGISTREER_GAST_CONFIRM
            gast.geslacht_str = GESLACHT2STR[gast.geslacht]
            context['gast'] = gast

        else:
            # onverwacht
            raise Http404('Verkeerde fase')

        # noteer: geen kruimels
        return render(request, template_name, context)

    @staticmethod
    def _maak_sporter_gast(gast, account):
        """ Voltooi het gast-account door het Sporter record aan te maken """

        aantal = Sporter.objects.filter(lid_nr=gast.lid_nr).count()
        if aantal == 0:
            date_now = timezone.now().date()
            ver_extern = Vereniging.objects.get(ver_nr=settings.EXTERN_VER_NR)

            sporter = Sporter(
                        lid_nr=gast.lid_nr,
                        wa_id=gast.wa_id,
                        voornaam=gast.voornaam,
                        achternaam=gast.achternaam,
                        unaccented_naam=maak_unaccented(gast.voornaam + ' ' + gast.achternaam),
                        email=gast.email,
                        telefoon=gast.telefoon,
                        geboorte_datum=gast.geboorte_datum,
                        geboorteplaats='',
                        geslacht=gast.geslacht,
                        adres_code=gast.lid_nr,     # voorkom match
                        para_classificatie='',
                        is_actief_lid=True,
                        sinds_datum=date_now,
                        bij_vereniging=ver_extern,
                        lid_tot_einde_jaar=date_now.year,
                        is_gast=True,
                        account=account)
            sporter.save()

            gast.sporter = sporter
            gast.save(update_fields=['sporter'])

    # @staticmethod
    # def _informeer_sec(gast):
    #
    #     functie_sec = Functie.objects.get(rol='SEC', vereniging__ver_nr=settings.EXTERN_VER_NR)
    #
    #     now = timezone.now()
    #     stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
    #     taak_deadline = now + datetime.timedelta(days=7)
    #     taak_tekst = "Er is zojuist een nieuwe gast-account aangemaakt. Het bondsnummer is %s.\n" % gast.lid_nr
    #     taak_tekst += "Als secretaris van vereniging %s kan je de details inzien." % settings.EXTERN_VER_NR
    #     taak_onderwerp = "Nieuw gast-account %s" % gast.lid_nr
    #     taak_log = "[%s] Taak aangemaakt" % stamp_str
    #
    #     # maak een taak aan voor deze BKO
    #     maak_taak(toegekend_aan_functie=functie_sec,
    #               deadline=taak_deadline,
    #               aangemaakt_door=None,  # systeem
    #               onderwerp=taak_onderwerp,
    #               beschrijving=taak_tekst,
    #               log=taak_log)

    def post(self, request, *args, **kwargs):
        """ wordt aangeroepen als de OPSLAAN knop gebruikt wordt op het formulier
            om een nieuw wachtwoord op te geven.
        """
        gast = self.gast

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')

        if gast.fase == REGISTRATIE_FASE_PASS:

            nieuw_ww = request.POST.get('pass', '')[:50]      # afkappen voor extra veiligheid

            # controleer het nieuwe wachtwoord
            valid, errmsg = account_test_wachtwoord_sterkte(nieuw_ww, self.account.username)

            if not valid:
                context = {
                    'foutmelding': errmsg,
                    'toon_tip': True,
                    'account': self.account
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_WACHTWOORD, context)

            # wijzigen van het wachtwoord zorgt er ook voor dat alle sessies van deze gebruiker vervallen
            # hierdoor blijft de gebruiker niet ingelogd op andere sessies
            self.account.set_password(nieuw_ww)      # does not save the account
            self.account.save()

            # houd de gebruiker ingelogd in deze sessie
            update_session_auth_hash(request, self.account)
            # bovenstaande maakt een nieuwe sessie aan, waardoor de eerstvolgende GET de sessie aanpast en schrijft

            gast.logboek += '[%s] Wachtwoord is gezet\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_CLUB
            gast.save(update_fields=['logboek', 'fase'])

        elif gast.fase == REGISTRATIE_FASE_CLUB:

            club = request.POST.get('club', '')[:100]       # afkappen voor extra veiligheid
            plaats = request.POST.get('plaats', '')[:50]    # afkappen voor extra veiligheid

            club = scrub_input_name(club)
            plaats = scrub_input_name(plaats)

            # naam: ARC, NHB, OGIO
            # plaats: Epe, Ede, Ee, As
            is_valid = len(club) >= 3 and len(plaats) >= 2

            if not is_valid:
                context = {
                    'foutmelding': 'niet alle velden zijn goed ingevuld',
                    'club': club,
                    'plaats': plaats,
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_CLUB, context)

            gast.club = club
            gast.club_plaats = plaats
            gast.logboek += '[%s] Vereniging naam, plaats zijn ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_LAND
            gast.save(update_fields=['club', 'club_plaats', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_LAND:

            land = request.POST.get('land', '')[:100]      # afkappen voor extra veiligheid
            bond = request.POST.get('bond', '')[:100]      # afkappen voor extra veiligheid
            lid_nr = request.POST.get('lid_nr', '')[:25]   # afkappen voor extra veiligheid

            land = scrub_input_name(land)
            bond = scrub_input_name(bond)

            # land: Chad, Cuba, Iran, Fiji
            # bond: Afkortingen, zoals RBA en DSB
            is_valid = len(land) >= 4 and len(bond) >= 3 and len(lid_nr) >= 3

            if not is_valid:
                context = {
                    'foutmelding': 'niet alle velden zijn goed ingevuld',
                    'land': land,
                    'bond': bond,
                    'lid_nr': lid_nr,
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_LAND_BOND_NR, context)

            gast.land = land
            gast.eigen_sportbond_naam = bond
            gast.eigen_lid_nummer = lid_nr
            gast.logboek += '[%s] Land, bond, lid_nr zijn ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_AGE
            gast.save(update_fields=['land', 'eigen_sportbond_naam', 'eigen_lid_nummer', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_AGE:

            jaar = request.POST.get('jaar', '')[:4]     # afkappen voor extra veiligheid
            maand = request.POST.get('maand', '')[:2]   # afkappen voor extra veiligheid
            dag = request.POST.get('dag', '')[:2]       # afkappen voor extra veiligheid

            is_valid = True

            try:
                jaar_nr = int(jaar)
            except ValueError:
                is_valid = False
                jaar = ''
                jaar_nr = 0

            try:
                maand_nr = int(maand)
            except ValueError:
                is_valid = False
                maand = ''
                maand_nr = 0

            try:
                dag_nr = int(dag)
            except ValueError:
                is_valid = False
                dag = ''
                dag_nr = 0

            datum = '2000-01-01'
            if is_valid:
                is_valid = 1900 < jaar_nr < 2100 and 1 <= maand_nr <= 12 and 1 <= dag_nr <= 31
                if is_valid:
                    datum = datetime.datetime.strptime('%d-%d-%d' % (jaar_nr, maand_nr, dag_nr), '%Y-%m-%d')

            if not is_valid:
                context = {
                    'foutmelding': 'niet alle velden zijn goed ingevuld',
                    'jaar': jaar,
                    'maand': maand,
                    'dag': dag,
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_AGE, context)

            gast.geboorte_datum = datum
            gast.logboek += '[%s] Geboortedatum is ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_TEL
            gast.save(update_fields=['geboorte_datum', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_TEL:

            tel = request.POST.get('tel', '')[:25]      # afkappen voor extra veiligheid

            is_valid = len(tel) > 10 and tel[0] == '+' and tel.count('+') == 1 and tel.count('-') <= 1
            try:
                # after removing +-*# and spaces, the phone number should be a number
                clean_tel = tel.replace(' ', '').replace('-', '').replace('+', '').replace('*', '').replace('#', '')
                _ = int(clean_tel)
            except ValueError:
                is_valid = False

            if not is_valid:
                context = {
                    'foutmelding': 'niet alle velden zijn goed ingevuld',
                    'tel': tel
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_TEL, context)

            gast.telefoon = tel
            gast.logboek += '[%s] Telefoonnummer is ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_WA_ID
            gast.save(update_fields=['telefoon', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_WA_ID:

            wa_id = request.POST.get('wa_id', '')[:8]      # afkappen voor extra veiligheid

            gast.wa_id = wa_id
            gast.logboek += '[%s] World Archery ID is ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_GENDER
            gast.save(update_fields=['wa_id', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_GENDER:

            gender = request.POST.get('gender', '')[:1]      # afkappen voor extra veiligheid

            is_valid = gender in ('M', 'V')

            if not is_valid:
                context = {
                    'foutmelding': 'niet alle velden zijn goed ingevuld',
                }

                # noteer: geen kruimels
                return render(request, TEMPLATE_REGISTREER_GAST_GENDER, context)

            gast.geslacht = gender
            gast.logboek += '[%s] Geslacht is ingevoerd\n' % stamp_str
            gast.fase = REGISTRATIE_FASE_CONFIRM
            gast.save(update_fields=['geslacht', 'fase', 'logboek'])

        elif gast.fase == REGISTRATIE_FASE_CONFIRM:

            bevestigd = request.POST.get('bevestigd', '')[:3]       # afkappen voor extra veiligheid

            if bevestigd == 'Ja':
                # gebruiker heeft op 'Ja' gedrukt

                self._maak_sporter_gast(gast, self.account)

                gast.logboek += '[%s] Toestemming opslaan ontvangen\n' % stamp_str
                gast.fase = REGISTRATIE_FASE_COMPLEET
                gast.save(update_fields=['fase', 'logboek'])

                # informeer de secretaris over de nieuwe registratie
                # self._informeer_sec(gast)

                # stuur de sporter door naar Mijn Pagina, om de voorkeuren aan te passen
                return HttpResponseRedirect(reverse('Sporter:profiel'))

            elif bevestigd == "Nee":
                # nog een rondje langs alle instellingen
                gast.logboek += "[%s] Gebruiker will gegeven wijzigen\n" % stamp_str
                gast.fase = REGISTRATIE_FASE_CLUB
                gast.save(update_fields=['fase', 'logboek'])

        else:
            raise Http404('Verkeerde fase')

        return HttpResponseRedirect(reverse('Registreer:gast-volgende-vraag'))

# end of file
