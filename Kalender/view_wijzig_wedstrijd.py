# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Taken.taken import maak_taak
from .models import (KalenderWedstrijd,
                     WEDSTRIJD_DISCIPLINE_TO_STR, WEDSTRIJD_STATUS_TO_STR, WEDSTRIJD_WA_STATUS_TO_STR,
                     WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, WEDSTRIJD_STATUS_GEACCEPTEERD,
                     WEDSTRIJD_STATUS_GEANNULEERD, WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B)
import datetime
from types import SimpleNamespace

TEMPLATE_KALENDER_WIJZIG_WEDSTRIJD = 'kalender/wijzig-wedstrijd.dtl'


class WijzigKalenderWedstrijdView(UserPassesTestMixin, View):

    """ Via deze view kan de HWL een wedstrijd van de vereniging wijzigen """

    # class variables shared by all instances
    template_name = TEMPLATE_KALENDER_WIJZIG_WEDSTRIJD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_HWL)

    def get(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de GET request af te handelen """
        context = dict()

        try:
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .get(pk=kwargs['wedstrijd_pk']))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        context['wed'] = wedstrijd

        context['now'] = now = timezone.now()
        context['begin_jaar'] = min(now.year, wedstrijd.datum_begin.year)     # zorg dat de huidige datum weer gekozen kan worden

        context['min_date'] = min(datetime.date(now.year, now.month, now.day), wedstrijd.datum_begin)
        context['max_date'] = datetime.date(now.year + 1, 12, 31)

        context['opt_status'] = opt_status = list()
        for code, status_str in WEDSTRIJD_STATUS_TO_STR.items():
            opt = SimpleNamespace()
            opt.status_str = status_str
            opt.selected = (code == wedstrijd.status)
            opt_status.append(opt)
        # for

        if self.rol_nu == Rollen.ROL_HWL:
            if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
                context['url_next_tekst'] = 'Vraag om goedkeuring'
                context['url_next_status'] = reverse('Kalender:zet-status',
                                                     kwargs={'wedstrijd_pk': wedstrijd.pk})
            else:
                context['limit_edits'] = True

        if self.rol_nu == Rollen.ROL_BB:
            if wedstrijd.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING:
                context['url_prev_tekst'] = 'Afkeuren'
                context['url_next_tekst'] = 'Accepteren'
                context['url_next_status'] = reverse('Kalender:zet-status',
                                                     kwargs={'wedstrijd_pk': wedstrijd.pk})

            elif wedstrijd.status == WEDSTRIJD_STATUS_GEACCEPTEERD:
                context['url_annuleer'] = reverse('Kalender:zet-status',
                                                  kwargs={'wedstrijd_pk': wedstrijd.pk})

        if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
            context['limit_edits'] = True
            context['block_edits'] = True
            context['niet_verwijderbaar'] = True

        # bereken hoeveel dagen de wedstrijd duurt
        duur_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
        context['duur_dagen'] = duur_dagen

        context['opt_duur'] = opt_duur = list()
        for lp in range(5):
            opt = SimpleNamespace()
            dagen = lp + 1
            opt.sel = "duur_%s" % dagen
            if dagen == 1:
                opt.keuze_str = '1 dag'
            else:
                opt.keuze_str = '%s dagen' % dagen

            opt.selected = (dagen == duur_dagen)

            opt_duur.append(opt)
        # for

        context['opt_locatie'] = opt_locatie = list()
        for locatie in wedstrijd.organiserende_vereniging.wedstrijdlocatie_set.exclude(zichtbaar=False).order_by('pk'):
            locatie.sel = "loc_%s" % locatie.pk
            locatie.selected = (wedstrijd.locatie == locatie)
            opt_locatie.append(locatie)
        # for

        wedstrijd.disc_str = WEDSTRIJD_DISCIPLINE_TO_STR[wedstrijd.discipline]
        context['opt_disc'] = opt_disc = list()
        for afk, disc in WEDSTRIJD_DISCIPLINE_TO_STR.items():
            opt = SimpleNamespace()
            opt.sel = 'disc_%s' % afk
            opt.keuze_str = disc
            opt.selected = (wedstrijd.discipline == afk)
            opt_disc.append(opt)
        # for

        wedstrijd.wa_status_str = WEDSTRIJD_WA_STATUS_TO_STR[wedstrijd.wa_status]
        context['opt_wa'] = opt_wa = list()
        for afk, descr in WEDSTRIJD_WA_STATUS_TO_STR.items():
            opt = SimpleNamespace()
            opt.sel = 'wa_%s' % afk
            opt.keuze_str = descr
            opt.selected = (wedstrijd.wa_status == afk)
            opt.disabled = (afk == WEDSTRIJD_WA_STATUS_A and not wedstrijd.voorwaarden_a_status_acceptatie)
            opt_wa.append(opt)
        # for

        context['url_voorwaarden'] = settings.VOORWAARDEN_A_STATUS_URL

        # aantal banen waar uit gekozen kan worden
        context['opt_banen'] = [nr for nr in range(2, 80 + 1)]  # 1 baan = handmatig in .dtl

        context['url_opslaan'] = reverse('Kalender:wijzig-wedstrijd',
                                         kwargs={'wedstrijd_pk': wedstrijd.pk})

        if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
            context['url_verwijder'] = context['url_opslaan']

        if self.rol_nu == Rollen.ROL_HWL:
            context['url_terug'] = reverse('Kalender:vereniging')
        else:
            context['url_terug'] = reverse('Kalender:manager')

        menu_dynamics(self.request, context, actief='kalender')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        try:
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .get(pk=kwargs['wedstrijd_pk']))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rollen.ROL_HWL and wedstrijd.organiserende_vereniging != self.functie_nu.nhb_ver:
            raise PermissionDenied('Wedstrijd niet van jouw vereniging')

        limit_edits = False
        block_edits = False
        if self.rol_nu == Rollen.ROL_HWL and wedstrijd.status != WEDSTRIJD_STATUS_ONTWERP:
            limit_edits = True

        if wedstrijd.status == WEDSTRIJD_STATUS_GEANNULEERD:
            limit_edits = True
            block_edits = True

        # verwijderen alleen toestaan in de ontwerp fase
        if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP and request.POST.get('verwijder_wedstrijd'):
            wedstrijd.delete()
        else:
            wedstrijd.titel = request.POST.get('titel', wedstrijd.titel)[:50]

            if not limit_edits:
                datum_ymd = request.POST.get('datum_begin', '')[:10]    # afkappen voor de veiligheid
                if datum_ymd:
                    try:
                        datum = datetime.datetime.strptime(datum_ymd, '%Y-%m-%d')
                    except ValueError:
                        raise Http404('Geen valide datum')

                    datum = datetime.date(datum.year, datum.month, datum.day)
                    now = timezone.now()
                    min_date = min(datetime.date(now.year, now.month, now.day), wedstrijd.datum_begin)
                    max_date = datetime.date(now.year + 1, 12, 31)
                    if min_date <= datum <= max_date:
                        wedstrijd.datum_begin = datum

            if not limit_edits:
                duur = request.POST.get('wedstrijd_duur', '')
                if duur.startswith('duur_'):
                    try:
                        duur = int(duur[5:10])      # afkappen voor de veiligheid
                    except ValueError:
                        raise Http404('Fout in wedstrijd duur')

                    wedstrijd.datum_einde = wedstrijd.datum_begin
                    duur -= 1
                    if 1 <= duur < 5:
                        wedstrijd.datum_einde += datetime.timedelta(days=duur)

            if not limit_edits:
                disc = request.POST.get('discipline', '')
                for afk in WEDSTRIJD_DISCIPLINE_TO_STR.keys():
                    if disc == 'disc_' + afk:
                        wedstrijd.discipline = afk
                # for

            if not limit_edits:
                wa_status = request.POST.get('wa_status', '')
                if wa_status == 'wa_%s' % WEDSTRIJD_WA_STATUS_B:
                    wedstrijd.wa_status = WEDSTRIJD_WA_STATUS_B

                elif wa_status == 'wa_%s' % WEDSTRIJD_WA_STATUS_A:
                    # moet eerst akkoord zijn gegaan met de voorwaarden
                    akkoord = request.POST.get('akkoord_a_status', '')
                    if akkoord:
                        account = request.user
                        lid = account.nhblid_set.all()[0]
                        wedstrijd.voorwaarden_a_status_who = "[%s] %s" % (lid.nhb_nr, lid.volledige_naam())
                        wedstrijd.voorwaarden_a_status_when = timezone.now()
                        wedstrijd.voorwaarden_a_status_acceptatie = True

                    if wedstrijd.voorwaarden_a_status_acceptatie:
                        wedstrijd.wa_status = WEDSTRIJD_WA_STATUS_A

            if not block_edits:
                wedstrijd.contact_naam = request.POST.get('contact_naam', wedstrijd.contact_naam)[:50]
                wedstrijd.contact_email = request.POST.get('contact_email', wedstrijd.contact_email)[:150]
                wedstrijd.contact_website = request.POST.get('contact_website', wedstrijd.contact_website)[:100]
                wedstrijd.contact_telefoon = request.POST.get('contact_telefoon', wedstrijd.contact_telefoon)[:50]

                aantal_banen = request.POST.get('aantal_banen', str(wedstrijd.aantal_banen))
                try:
                    aantal_banen = int(aantal_banen[:5])        # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Fout in aantal banen')

                if 1 <= aantal_banen <= 100:
                    wedstrijd.aantal_banen = aantal_banen

                wedstrijd.scheidsrechters = request.POST.get('scheidsrechters', wedstrijd.scheidsrechters)[:500]

            wedstrijd.save()

        if self.rol_nu == Rollen.ROL_HWL:
            url = reverse('Kalender:vereniging')
        else:
            url = reverse('Kalender:manager')

        return HttpResponseRedirect(url)


class ZetStatusKalenderWedstrijdView(UserPassesTestMixin, View):
    """ Via deze view kan de BB of HWL de wedstrijd status aanpassen """

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rollen.ROL_BB, Rollen.ROL_HWL)

    @staticmethod
    def _maak_taak_voor_bb(wedstrijd, msg):
        now = timezone.now()
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % now
        taak_tekst = msg % "%s van vereniging %s" % (repr(wedstrijd.titel), wedstrijd.organiserende_vereniging)
        taak_tekst += '\n\nGa naar de Wedstrijdkalender om deze wedstrijd te behandelen.'

        # maak de persoonlijke taak aan voor ieder account met is_BB vlag
        # FUTURE: omzetten naar taak voor rol BB
        for account in Account.objects.filter(is_BB=True):
            maak_taak(
                toegekend_aan=account,
                deadline=taak_deadline,
                beschrijving=taak_tekst,
                handleiding_pagina='',
                log=taak_log)
        # for

    @staticmethod
    def _maak_taak_voor_hwl(wedstrijd, msg):
        now = timezone.now()
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % now
        taak_tekst = msg % repr(wedstrijd.titel)
        taak_tekst += '\n\nGa naar de Wedstrijdkalender om deze wedstrijd te behandelen.'

        functie_hwl = wedstrijd.organiserende_vereniging.functie_set.filter(rol='HWL')[0]

        # maak de persoonlijke taak aan voor ieder account gekoppeld aan deze functie
        # FUTURE: omzetten naar taak voor rol HWL
        for account in functie_hwl.accounts.all():
            maak_taak(
                toegekend_aan=account,
                deadline=taak_deadline,
                beschrijving=taak_tekst,
                handleiding_pagina='',
                log=taak_log)
        # for

    def post(self, request, *args, **kwargs):

        try:
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .get(pk=kwargs['wedstrijd_pk']))
        except KalenderWedstrijd.DoesNotExist:
            raise Http404('Wedstrijd niet gevonden')

        terug = request.POST.get('terug', '')
        verder = request.POST.get('verder', '')
        annuleer = request.POST.get('annuleer', '')

        # TODO: zet wijzigingen in het logboek, of begin een logboekje per wedstrijd

        if self.rol_nu == Rollen.ROL_HWL:
            if wedstrijd.organiserende_vereniging != self.functie_nu.nhb_ver:
                raise PermissionDenied('Wedstrijd niet van jouw vereniging')

            next_url = reverse('Kalender:vereniging')

            if wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP and verder:
                # verzoek tot goedkeuring
                wedstrijd.status = WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING
                wedstrijd.save()
                # maak een taak aan voor de BB
                self._maak_taak_voor_bb(wedstrijd, 'Wedstrijd %s is ingediende voor goedkeuring')

        else:
            next_url = reverse('Kalender:manager')

            if annuleer:
                # annuleer deze wedstrijd
                wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
                wedstrijd.save()

                # maak een taak aan voor de HWL
                self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geannuleerd")

            elif wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
                if verder:
                    wedstrijd.status = WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING
                    wedstrijd.save()

            elif wedstrijd.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING:
                if terug:
                    # afgekeurd --> terug naar ontwerp
                    wedstrijd.status = WEDSTRIJD_STATUS_ONTWERP
                    wedstrijd.save()
                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is terug gezet naar de status 'ontwerp'")

                elif verder:
                    # goedgekeurd --> naar geaccepteerd
                    wedstrijd.status = WEDSTRIJD_STATUS_GEACCEPTEERD
                    wedstrijd.save()

                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geaccepteerd en openbaar")

        return HttpResponseRedirect(next_url)

# end of file
