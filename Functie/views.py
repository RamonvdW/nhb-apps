# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.shortcuts import render
from django.db.models import Q, Value, CharField
from django.db.models.functions import Concat, Cast
from django.views.generic import ListView, View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from NhbStructuur.models import NhbLid
from Plein.menu import menu_dynamics
from Logboek.models import schrijf_in_logboek
from Overig.tijdelijke_url import maak_tijdelijke_url_functie_email
from Mailer.models import mailer_queue_email
from Overig.tijdelijke_url import set_tijdelijke_url_receiver, RECEIVER_BEVESTIG_FUNCTIE_EMAIL
from Overig.helpers import get_safe_from_ip
from .rol import Rollen, rol_get_huidige, rol_get_huidige_functie, rol_get_beschrijving
from .models import Functie
from .forms import ZoekBeheerdersForm, WijzigBeheerdersForm, WijzigEmailForm


TEMPLATE_OVERZICHT = 'functie/overzicht.dtl'
TEMPLATE_OVERZICHT_VERENIGING = 'functie/overzicht-vereniging.dtl'
TEMPLATE_WIJZIG = 'functie/wijzig.dtl'
TEMPLATE_WIJZIG_EMAIL = 'functie/wijzig-email.dtl'
TEMPLATE_BEVESTIG_EMAIL = 'functie/bevestig.dtl'
TEMPLATE_EMAIL_BEVESTIGD = 'functie/bevestigd.dtl'


def mag_beheerder_wijzigen_of_403(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigView (koppelen van leden aan 1 functie) - tijdens get_queryset()
            OntvangWijzigingenView - vroeg in afhandelen POST verzoek
    """

    # test_func van WijzigView laat alleen BB, BKO, RKO of HWL door
    # OntvangWijzigingenView heeft niet zo'n filter

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    if rol_nu == Rollen.ROL_BB:
        # BB mag BKO koppelen
        if functie.rol != 'BKO':
            raise PermissionDenied()
        return

    if rol_nu == Rollen.ROL_SEC:
        if functie.nhb_ver != functie_nu.nhb_ver:
            # verkeerde vereniging
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol not in ('SEC', 'HWL'):
            # niet een rol die de SEC mag wijzigen
            raise PermissionDenied()

        # SEC
        return

    if rol_nu == Rollen.ROL_HWL:
        if functie.nhb_ver != functie_nu.nhb_ver:
            # verkeerde vereniging
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol not in ('HWL', 'WL'):
            # niet een rol die de HWL mag wijzigen
            raise PermissionDenied()

        # HWL
        return

    # RCL mag HWL en WL koppelen van vereniging binnen regio RCL
    if rol_nu == Rollen.ROL_RCL and functie.rol in ('HWL', 'WL'):
        if functie_nu.nhb_regio != functie.nhb_ver.regio:
            raise PermissionDenied('Verkeerde regio')
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if not functie_nu or functie_nu.comp_type != functie.comp_type:
        # SEC/HWL/WL verdwijnt hier ook
        raise PermissionDenied('Verkeerde competitie')

    if rol_nu == Rollen.ROL_BKO:
        if functie.rol != 'RKO':
            raise PermissionDenied()
        return

    elif rol_nu == Rollen.ROL_RKO:
        if functie.rol != 'RCL':
            raise PermissionDenied()

        # controleer of deze regio gewijzigd mag worden
        if functie.nhb_regio.rayon != functie_nu.nhb_rayon:
            raise PermissionDenied('Verkeerde rayon')
        return

    # niets hier te zoeken (RCL en andere rollen)
    raise PermissionDenied()


def mag_email_wijzigen_of_403(request, functie):
    """ Stuur gebruiker weg als illegaal van de aanroepende view gebruik gemaakt wordt

        Wordt gebruikt door:
            WijzigEmailView - tijdens GET en POST
    """

    # test_func van WijzigEmailView laat alleen BB, BKO, RKO, RCL, SEC en HWL door

    rol_nu, functie_nu = rol_get_huidige_functie(request)

    # rol mag direct onderliggende functie aanpassen:
    #   BB --> alle BKO
    #   BKO (comp_type) --> alle RKO (comp_type)
    #   RKO (comp_type) --> alle RCL (comp_type) in zijn rayon

    # special voor BB, want dat is geen functie
    if rol_nu == Rollen.ROL_BB:
        # BB mag BKO email aanpassen
        if functie.rol != 'BKO':
            raise PermissionDenied()
        return

    # voor de rest moet de gebruiker een functie bezitten
    if not functie_nu:
        raise PermissionDenied()     # pragma: no cover

    # SEC en HWL mogen email van HWL en WL aanpassen
    if rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL):
        # alleen binnen eigen vereniging
        if functie_nu.nhb_ver != functie.nhb_ver:
            raise PermissionDenied('Verkeerde vereniging')

        if functie.rol not in ('HWL', 'WL'):
            # hier verdwijnt SEC in het putje
            # secretaris email is alleen aan te passen via Onze Relaties
            raise PermissionDenied()

        return

    # alle rollen mogen hun eigen e-mailadres aanpassen
    if functie_nu == functie:
        return

    # RCL mag email van HWL en WL aanpassen van vereniging binnen regio RCL
    if rol_nu == Rollen.ROL_RCL and functie.rol in ('HWL', 'WL'):
        if functie_nu.nhb_regio != functie.nhb_ver.regio:
            raise PermissionDenied('Verkeerde regio')
        return

    # BKO, RKO, RCL

    # controleer dat deze wijziging voor de juiste competitie is
    # (voorkomt BKO 25m 1pijl probeert RKO Indoor te koppelen)
    if functie_nu.comp_type != functie.comp_type:
        raise PermissionDenied('Verkeerde competitie')

    if rol_nu == Rollen.ROL_BKO:
        if functie.rol != 'RKO':
            raise PermissionDenied()
        return

    elif rol_nu == Rollen.ROL_RKO:
        if functie.rol != 'RCL':
            raise PermissionDenied()

        # controleer of deze regio gewijzigd mag worden
        if functie.nhb_regio.rayon != functie_nu.nhb_rayon:
            raise PermissionDenied('Verkeerde rayon')
        return

    # niets hier te zoeken
    raise PermissionDenied()


def receive_bevestiging_functie_email(request, functie):
    """ deze functie wordt aangeroepen als een tijdelijke url gevolgd wordt
        om een nieuw email adres te bevestigen voor een functie.

        We moeten een url teruggeven waar een http-redirect naar gedaan kan worden
        of een HttpResponse object.
    """

    # het is mogelijk om meerdere keren hetzelfde e-mailadres te koppelen
    # je hebt dan meerdere mails met tijdelijke urls om te volgen
    # deze functie wordt voor elke gevolgde url aangeroepen
    # na de eerste keer is nieuwe_email leeg en gebeurt er niets
    # we geven wel steeds het succes verhaal terug
    if functie.nieuwe_email:
        # schrijf in het logboek
        from_ip = get_safe_from_ip(request)
        msg = "Bevestigd vanaf IP %s voor functie %s" % (from_ip, functie.beschrijving)
        schrijf_in_logboek(account=None,
                           gebruikte_functie="Bevestig e-mail",
                           activiteit=msg)

        # zet het e-mailadres door
        functie.bevestigde_email = functie.nieuwe_email
        functie.nieuwe_email = ''
        functie.save()

    context = {'functie': functie}
    return render(request, TEMPLATE_EMAIL_BEVESTIGD, context)


set_tijdelijke_url_receiver(RECEIVER_BEVESTIG_FUNCTIE_EMAIL, receive_bevestiging_functie_email)


def functie_vraag_email_bevestiging(functie):
    """ Stuur een mail naar het adres om te vragen om een bevestiging.
        Gebruik een tijdelijke URL die, na het volgen, weer in deze module uit komt.
    """

    # maak de url aan om het e-mailadres te bevestigen
    url = maak_tijdelijke_url_functie_email(functie)

    text_body = ("Hallo!\n\n"
                 + "Een beheerder heeft dit e-mailadres gekoppeld op de website van de NHB.\n"
                 + "Klik op onderstaande link om dit te bevestigen.\n\n"
                 + url + "\n\n"
                 + "Als je dit niet herkent, neem dan contact met ons op via info@handboogsport.nl\n\n"
                 + "Het bondsburo\n")

    mailer_queue_email(functie.nieuwe_email,
                       'Bevestig gebruik e-mail voor rol',
                       text_body,
                       enforce_whitelist=False)


class WijzigEmailView(UserPassesTestMixin, View):

    """ Via deze view kan het e-mailadres van een functie aangepast worden """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_SEC, Rollen.ROL_HWL)

    def _get_functie_or_404(self):
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Foutieve functie')
        return functie

    def _render_form(self, form, functie):
        context = dict()
        context['functie'] = functie

        if self.rol_nu == Rollen.ROL_HWL:
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
            menu_dynamics(self.request, context, actief='vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
            menu_dynamics(self.request, context, actief='hetplein')

        context['form'] = form
        context['form_submit_url'] = reverse('Functie:wijzig-email', kwargs={'functie_pk': functie.pk})

        return render(self.request, TEMPLATE_WIJZIG_EMAIL, context)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een GET request ontvangen is
        """
        functie = self._get_functie_or_404()

        # TODO: functie.nieuwe_email opruimen als SiteTijdelijkeUrl verlopen is (of opgeruimd is)

        # BKO, RKO, RCL, HWL mogen hun eigen contactgegevens wijzigen
        # als ze de rol aangenomen hebben
        # verder mogen ze altijd de onderliggende laag aanpassen (net als beheerders koppelen)
        mag_email_wijzigen_of_403(self.request, functie)
        form = WijzigEmailForm()
        return self._render_form(form, functie)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de OPSLAAN knop van het formulier.
        """
        functie = self._get_functie_or_404()
        mag_email_wijzigen_of_403(self.request, functie)

        form = WijzigEmailForm(self.request.POST)
        if not form.is_valid():
            # geeft het invulformulier terug voor de foutmelding + nieuwe poging
            form.add_error(None, 'E-mailadres niet geaccepteerd')
            return self._render_form(form, functie)

        # sla het nieuwe e-mailadres op
        functie.nieuwe_email = form.cleaned_data['email']
        functie.save()

        account = self.request.user
        schrijf_in_logboek(account, 'Rollen', 'Nieuw e-mailadres ingevoerd voor rol %s' % functie.beschrijving)

        # stuur email
        # (extra args zijn input voor hash, om unieke url te krijgen)
        functie_vraag_email_bevestiging(functie)

        context = dict()
        context['functie'] = functie

        # stuur terug naar het overzicht
        if self.rol_nu == Rollen.ROL_HWL:
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')

        return render(request, TEMPLATE_BEVESTIG_EMAIL, context)


class OntvangBeheerderWijzigingenView(View):

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        raise Http404()

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als een POST request ontvangen is.
            dit is gekoppeld aan het drukken op de Registreer knop.
        """
        functie_pk = self.kwargs['functie_pk']
        try:
            functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Verkeerde functie')

        mag_beheerder_wijzigen_of_403(request, functie)

        form = WijzigBeheerdersForm(request.POST)
        form.full_clean()  # vult cleaned_data
        add = form.cleaned_data.get('add')
        drop = form.cleaned_data.get('drop')

        if add:
            account_pk = add
        elif drop:
            account_pk = drop
        else:
            raise Http404()

        try:
            account = Account.objects.get(pk=account_pk)
        except Account.DoesNotExist:
            raise Http404('Account niet gevonden')

        if account.nhblid_set.count() > 0:
            nhblid = account.nhblid_set.all()[0]
            wie = "NHB lid %s (%s)" % (nhblid.nhb_nr, nhblid.volledige_naam())
        else:
            nhblid = None
            wie = "Account %s" % account.get_account_full_name()

        if add:
            rol_nu, functie_nu = rol_get_huidige_functie(request)
            if rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL):
                # stel zeker dat nhblid lid is bij de vereniging van functie
                if not nhblid or nhblid.bij_vereniging != functie.nhb_ver:
                    raise PermissionDenied('Geen lid van jouw vereniging')

            functie.accounts.add(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s is beheerder gemaakt voor functie %s" % (wie, functie.beschrijving))
        else:
            functie.accounts.remove(account)
            schrijf_in_logboek(request.user, 'Rollen',
                               "%s losgekoppeld van functie %s" % (wie, functie.beschrijving))

        return HttpResponseRedirect(reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': functie.pk}))


class WijzigBeheerdersView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders voor een functie gekozen worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WIJZIG
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._form = None
        self._functie = None
        self._zoekterm = None
        self._huidige_beheerders = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol = rol_get_huidige(self.request)
        return rol in (Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_SEC, Rollen.ROL_HWL)

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        functie_pk = self.kwargs['functie_pk']
        try:
            self._functie = Functie.objects.get(pk=functie_pk)
        except Functie.DoesNotExist:
            # foutieve functie_pk
            raise Http404('Verkeerde functie')

        mag_beheerder_wijzigen_of_403(self.request, self._functie)

        self._form = ZoekBeheerdersForm(self.request.GET)
        self._form.full_clean()  # vult cleaned_data

        # huidige beheerders willen we niet opnieuw vinden
        beheerder_accounts = self._functie.accounts.all()
        for account in beheerder_accounts:
            account.geo_beschrijving = ''
            if account.nhblid_set.count() > 0:
                nhblid = account.nhblid_set.all()[0]
                regio = nhblid.bij_vereniging.regio
                if not regio.is_administratief:
                    account.geo_beschrijving = "regio %s / rayon %s" % (regio.regio_nr, regio.rayon.rayon_nr)
        self._huidige_beheerders = beheerder_accounts

        zoekterm = self._form.cleaned_data['zoekterm']
        if len(zoekterm) >= 2:  # minimaal twee tekens van de naam/nummer
            self._zoekterm = zoekterm

            # let op: we koppelen een account, maar zoeken een NHB lid,
            #         om te kunnen filteren op vereniging
            #         accounts die geen NhbLid zijn worden hier niet gevonden
            qset = (NhbLid
                    .objects
                    .exclude(account=None)
                    .exclude(is_actief_lid=False)
                    .exclude(account__in=beheerder_accounts)
                    .annotate(hele_reeks=Concat('voornaam', Value(' '), 'achternaam'))
                    .annotate(nhb_nr_str=Cast('nhb_nr', CharField()))
                    .filter(Q(nhb_nr_str__contains=zoekterm) |
                            Q(voornaam__icontains=zoekterm) |
                            Q(achternaam__icontains=zoekterm) |
                            Q(hele_reeks__icontains=zoekterm))
                    .order_by('nhb_nr'))

            is_vereniging_rol = (self._functie.rol in ('SEC', 'HWL', 'WL'))
            if is_vereniging_rol:
                # alleen leden van de vereniging laten kiezen
                qset = qset.filter(bij_vereniging=self._functie.nhb_ver)

            objs = list()
            for nhblid in qset[:50]:
                account = nhblid.account
                account.geo_beschrijving = ''
                account.nhb_nr_str = str(nhblid.nhb_nr)

                if is_vereniging_rol:
                    account.vereniging_naam = str(nhblid.bij_vereniging)    # [1234] Naam
                else:
                    regio = nhblid.bij_vereniging.regio
                    if not regio.is_administratief:
                        account.geo_beschrijving = "regio %s / rayon %s" % (regio.regio_nr, regio.rayon.rayon_nr)

                objs.append(account)
            # for

            return objs

        self._zoekterm = ""
        return None

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)
        context['functie'] = self._functie
        context['huidige_beheerders'] = self._huidige_beheerders
        context['rol_str'] = rol_get_beschrijving(self.request)
        context['wijzig_url'] = reverse('Functie:ontvang-wijzigingen', kwargs={'functie_pk': self._functie.pk})
        context['zoek_url'] = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': self._functie.pk})
        context['zoekterm'] = self._zoekterm
        context['form'] = self._form

        if self._functie.rol in ('SEC', 'HWL', 'WL'):
            context['is_vereniging_rol'] = True
            # TODO: fix terug-url. Je kan hier op twee manieren komen:
            # via Plein, Verenigingen, Details (=Vereniging:accommodaties/details/pk/pk/), Koppel beheerders
            # via Verenging, Beheerders (=Functie:overzicht-vereniging), Koppel beheerders
            context['terug_url'] = reverse('Functie:overzicht-vereniging')
            menu_dynamics(self.request, context, actief='vereniging')
        else:
            context['terug_url'] = reverse('Functie:overzicht')
            menu_dynamics(self.request, context, actief='hetplein')
        return context


class OverzichtVerenigingView(UserPassesTestMixin, ListView):

    """ Via deze view kunnen beheerders binnen een vereniging getoond en gewijzigd worden.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT_VERENIGING
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rollen.ROL_SEC, Rollen.ROL_HWL, Rollen.ROL_WL)

    @staticmethod
    def _sorteer(objs):
        lst = list()
        for obj in objs:
            if obj.rol == "SEC":
                nr = 1
            elif obj.rol == "HWL":
                nr = 2
            else:
                # obj.rol == "WL":
                nr = 3
            tup = (nr, obj)
            lst.append(tup)
        # for
        lst.sort()
        return [obj for _, obj in lst]

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        # en de huidige functie selecteert de vereniging
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # zoek alle rollen binnen deze vereniging
        objs = Functie.objects.filter(nhb_ver=functie_nu.nhb_ver)

        # zet beheerders en wijzig_url
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in
                              obj.accounts.only('username', 'first_name', 'last_name').all()]

            obj.wijzig_url = None
            obj.email_url = None

            mag_wijzigen = False
            if rol_nu == Rollen.ROL_SEC and obj.rol in ('SEC', 'HWL'):
                # SEC mag andere SEC and HWL koppelen
                mag_wijzigen = True
            elif rol_nu == Rollen.ROL_HWL and obj.rol in ('HWL', 'WL'):
                # HWL mag andere HWL en WL koppelen
                mag_wijzigen = True

            if mag_wijzigen:
                obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})
                # email voor secretaris komt uit Onze Relaties
                if obj.rol != 'SEC':
                    obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})
        # for

        return self._sorteer(objs)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        # als er geen wijzig knop in beeld hoeft te komen, dan kan de tabel wat smaller
        context['show_wijzig_kolom'] = False
        for obj in context['object_list']:
            if obj.wijzig_url:
                context['show_wijzig_kolom'] = True
                break   # from the for
        # for

        context['terug_url'] = reverse('Vereniging:overzicht')

        menu_dynamics(self.request, context, actief='vereniging')
        return context


class OverzichtView(UserPassesTestMixin, ListView):

    """ Via deze view worden de huidige beheerders getoond
        met Wijzig knoppen waar de gebruiker dit mag, aan de hand van de huidige rol

        Wordt ook gebruikt om de HWL relevante bestuurders te tonen
    """

    # class variables shared by all instances
    template_name = TEMPLATE_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # alle competitie beheerders + HWL
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB, Rollen.ROL_BKO, Rollen.ROL_RKO, Rollen.ROL_RCL, Rollen.ROL_HWL)

    @staticmethod
    def _sorteer_functies(objs):
        """ Sorteer de functies zodat:
            18 < 25
            BKO < RKO < RCL
            op volgorde van rayon- of regionummer (oplopend)
        """
        sort_level = {'BKO': 1,  'RKO': 2, 'RCL': 3}
        tup2obj = dict()
        sort_me = list()
        for obj in objs:
            if obj.rol == 'RKO':
                deel = obj.nhb_rayon.rayon_nr
            elif obj.rol == 'RCL':
                deel = obj.nhb_regio.regio_nr
            else:
                deel = 0

            tup = (obj.comp_type, sort_level[obj.rol], deel)
            sort_me.append(tup)
            tup2obj[tup] = obj
        # for
        sort_me.sort()
        objs = [tup2obj[tup] for tup in sort_me]
        return objs

    def _zet_wijzig_urls(self, objs):
        """ Voeg een wijzig_url veld toe aan elk Functie object
        """
        # de huidige rol bepaalt welke functies gewijzigd mogen worden
        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        rko_rayon_nr = None
        if rol_nu == Rollen.ROL_BB:
            wijzigbare_functie_rol = 'BKO'
        elif rol_nu == Rollen.ROL_BKO:
            wijzigbare_functie_rol = 'RKO'
        elif rol_nu == Rollen.ROL_RKO:
            wijzigbare_functie_rol = 'RCL'
            rko_rayon_nr = functie_nu.nhb_rayon.rayon_nr
        else:
            # beheerder kan niets wijzigen, maar inzien mag wel
            wijzigbare_functie_rol = "niets"

        for obj in objs:
            obj.wijzig_url = None
            if obj.rol == wijzigbare_functie_rol:
                # als BB mag je beide BKO's wijzigen
                # overige rollen alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if rol_nu == Rollen.ROL_BB or obj.comp_type == functie_nu.comp_type:
                    obj.wijzig_url = reverse('Functie:wijzig-beheerders', kwargs={'functie_pk': obj.pk})

                    # verdere begrenzing RKO: alleen 'zijn' Regio's
                    if rol_nu == Rollen.ROL_RKO and obj.rol == "RCL" and obj.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        obj.wijzig_url = None
        # for

        wijzigbare_functie = functie_nu
        if rol_nu == Rollen.ROL_BB:
            wijzigbare_email_rol = 'BKO'
        elif rol_nu == Rollen.ROL_BKO:
            wijzigbare_email_rol = 'RKO'
        elif rol_nu == Rollen.ROL_RKO:
            wijzigbare_email_rol = 'RCL'
            rko_rayon_nr = functie_nu.nhb_rayon.rayon_nr
        else:
            # beheerder kan niets wijzigen, maar inzien mag wel
            wijzigbare_email_rol = 'niets'

        for obj in objs:
            obj.email_url = None

            if obj == wijzigbare_functie:
                obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})
            elif obj.rol == wijzigbare_email_rol:
                # als BB mag je beide BKO's wijzigen
                # overige rollen alleen van hun eigen competitie type (Indoor / 25m1pijl)
                if rol_nu == Rollen.ROL_BB or obj.comp_type == functie_nu.comp_type:
                    obj.email_url = reverse('Functie:wijzig-email', kwargs={'functie_pk': obj.pk})

                    # verdere begrenzing RKO: alleen 'zijn' Regio's
                    if rol_nu == Rollen.ROL_RKO and obj.rol == "RCL" and obj.nhb_regio.rayon.rayon_nr != rko_rayon_nr:
                        obj.email_url = None
        # for

    @staticmethod
    def _zet_accounts(objs):
        """ als we de template door functie.accounts.all() laten lopen dan resulteert
            elke lookup in een database query voor het volledige account record.
            Hier doen we het iets efficienter.
        """
        for obj in objs:
            obj.beheerders = [account.volledige_naam() for account in obj.accounts.all()]
        # for

    def get_queryset(self):
        """ called by the template system to get the queryset or list of objects for the template """

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)

        # maak een lijst van de functies
        if rol_nu == Rollen.ROL_HWL:
            # toon alleen de hierarchy vanuit deze vereniging omhoog
            functie_hwl = functie_nu
            objs = (Functie.objects
                    .filter(Q(rol='RCL', nhb_regio=functie_hwl.nhb_ver.regio) |
                            Q(rol='RKO', nhb_rayon=functie_hwl.nhb_ver.regio.rayon) |
                            Q(rol='BKO'))
                    .select_related('nhb_rayon', 'nhb_regio', 'nhb_regio__rayon')
                    .prefetch_related('accounts'))
        else:
            objs = (Functie.objects
                    .filter(Q(rol='BKO') | Q(rol='RKO') | Q(rol='RCL'))
                    .select_related('nhb_rayon', 'nhb_regio', 'nhb_regio__rayon')
                    .prefetch_related('accounts'))

        objs = self._sorteer_functies(objs)

        # zet de wijzig urls, waar toegestaan
        self._zet_wijzig_urls(objs)
        self._zet_accounts(objs)
        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['huidige_rol'] = rol_get_beschrijving(self.request)

        if self.rol_nu == Rollen.ROL_HWL:
            context['rol_is_hwl'] = True

        if self.rol_nu in (Rollen.ROL_IT, Rollen.ROL_BB):
            context['accounts_it'] = (Account
                                      .objects
                                      .filter(is_staff=True)
                                      .order_by('username'))

            context['accounts_bb'] = (Account
                                      .objects
                                      .filter(is_BB=True)
                                      .order_by('username'))

        menu_dynamics(self.request, context, actief='hetplein')
        return context


# end of file
