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
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Functie.rol import Rollen, rol_get_huidige_functie
from Plein.menu import menu_dynamics
from Taken.taken import maak_taak
from Wedstrijden.models import BAAN_TYPE_BUITEN, BAAN_TYPE_EXTERN, WedstrijdLocatie
from .models import (KalenderWedstrijd,
                     WEDSTRIJD_DISCIPLINE_TO_STR, WEDSTRIJD_STATUS_TO_STR, WEDSTRIJD_WA_STATUS_TO_STR,
                     WEDSTRIJD_STATUS_ONTWERP, WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING, WEDSTRIJD_STATUS_GEACCEPTEERD,
                     WEDSTRIJD_STATUS_GEANNULEERD, WEDSTRIJD_WA_STATUS_A, WEDSTRIJD_WA_STATUS_B,
                     WEDSTRIJD_DUUR_MAX_DAGEN, WEDSTRIJD_BEGRENZING_TO_STR)
import datetime
from types import SimpleNamespace

TEMPLATE_KALENDER_WIJZIG_WEDSTRIJD = 'kalender/wijzig-wedstrijd.dtl'


class WijzigKalenderWedstrijdView(UserPassesTestMixin, View):

    """ Via deze view kunnen de HWL of BB een wedstrijd wijzigen """

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
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('sessies',
                                           'sessies__wedstrijdklassen',
                                           'wedstrijdklassen')
                         .get(pk=wedstrijd_pk))
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
        for lp in range(WEDSTRIJD_DUUR_MAX_DAGEN):
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

        context['opt_begrenzing'] = opt_begrenzing = list()
        for code, begrenzing_str in WEDSTRIJD_BEGRENZING_TO_STR.items():
            opt = SimpleNamespace()
            opt.sel = 'begrenzing_%s' % code
            opt.keuze_str = begrenzing_str
            opt.selected = (code == wedstrijd.begrenzing)
            if opt.selected:
                wedstrijd.begrenzing_str = begrenzing_str
            opt_begrenzing.append(opt)
        # for

        locaties = (wedstrijd
                    .organiserende_vereniging
                    .wedstrijdlocatie_set
                    .exclude(zichtbaar=False)
                    .order_by('pk'))
        try:
            binnen_locatie = locaties.get(adres_uit_crm=True)
        except WedstrijdLocatie.DoesNotExist:
            binnen_locatie = None

        max_banen = 1
        context['opt_locatie'] = opt_locatie = list()
        for locatie in locaties:
            # buitenbaan aanvullen met de gegevens van de accommodatie
            locatie.keuze_str = 'Binnen accommodatie'
            if locatie.baan_type == BAAN_TYPE_BUITEN:
                locatie.keuze_str = 'Buiten accommodatie'
                if not binnen_locatie:
                    # rare situatie: wel een buitenbaan, maar geen accommodatie
                    continue        # met de for
                locatie.adres = binnen_locatie.adres
                locatie.plaats = binnen_locatie.plaats
            elif locatie.baan_type == BAAN_TYPE_EXTERN:
                locatie.keuze_str = locatie.naam

            locatie.sel = "loc_%s" % locatie.pk
            locatie.selected = (wedstrijd.locatie == locatie)
            locatie.keuze_str += ': ' + locatie.adres.replace('\n', ', ') + ' [disciplines: %s]' % locatie.disciplines_str()
            opt_locatie.append(locatie)

            max_banen = max(locatie.banen_18m, locatie.banen_25m, locatie.buiten_banen, max_banen)
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

        # zoek uit welke wedstrijdklassen in gebruik zijn bij de sessies
        klassen_gebruikt = list()
        bogen_gebruikt = list()
        for sessie in wedstrijd.sessies.all():
            for klasse in sessie.wedstrijdklassen.select_related('boogtype').all():
                if klasse.pk not in klassen_gebruikt:
                    klassen_gebruikt.append(klasse.pk)
                    if klasse.boogtype.pk not in bogen_gebruikt:
                        bogen_gebruikt.append(klasse.boogtype.pk)
            # for
        # for

        context['opt_bogen'] = opt_bogen = list()
        pks = list(wedstrijd.boogtypen.values_list('pk', flat=True))
        for obj in BoogType.objects.order_by('volgorde'):
            obj.sel = 'boog_%s' % obj.afkorting
            obj.gebruikt = (obj.pk in bogen_gebruikt)
            obj.selected = (obj.pk in pks)
            opt_bogen.append(obj)
        # for

        context['opt_klasse_1'] = opt_klasse_1 = list()
        context['opt_klasse_2'] = opt_klasse_2 = list()
        context['wedstrijd_is_a_status'] = (wedstrijd.wa_status == WEDSTRIJD_WA_STATUS_A)
        pks = list(wedstrijd.wedstrijdklassen.values_list('pk', flat=True))
        for klasse in (KalenderWedstrijdklasse
                       .objects
                       .exclude(buiten_gebruik=True)
                       .select_related('leeftijdsklasse')
                       .order_by('volgorde')):

            klasse.sel = 'klasse_%s' % klasse.pk
            klasse.gebruikt = (klasse.pk in klassen_gebruikt)
            klasse.selected = (klasse.pk in pks)

            if klasse.leeftijdsklasse.geslacht == 'M':
                opt_klasse_1.append(klasse)
            else:
                opt_klasse_2.append(klasse)
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

        context['opt_aanwezig'] = aanwezig = list()
        for mins in (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
            opt = SimpleNamespace()
            opt.sel = 'aanwezig_%d' % mins
            opt.keuze_str = "%d minuten" % mins
            opt.selected = (wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn == mins)
            aanwezig.append(opt)
        # for

        context['url_voorwaarden'] = settings.VOORWAARDEN_A_STATUS_URL

        # aantal banen waar uit gekozen kan worden
        max_banen = min(80, max_banen)
        context['opt_banen'] = [nr for nr in range(2, max_banen + 1)]  # 1 baan = handmatig in .dtl

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

    @staticmethod
    def _verplaats_sessies(wedstrijd, oude_datum_begin):
        if wedstrijd.datum_begin == oude_datum_begin:
            return

        # bereken hoeveel dagen de wedstrijd verplaatst is
        delta = wedstrijd.datum_begin - oude_datum_begin

        # pas alle sessies aan met dezelfde hoeveelheid
        for sessie in wedstrijd.sessies.all():
            sessie.datum += delta
            sessie.save(update_fields=['datum'])
        # for

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen om de POST request af te handelen """

        try:
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'wedstrijdklassen',
                                           'sessies',
                                           'sessies__wedstrijdklassen')
                         .get(pk=wedstrijd_pk))
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
            oude_datum_begin = wedstrijd.datum_begin

            # zoek uit welke wedstrijdklassen in gebruik zijn bij de sessies
            klassen_pks_gebruikt_in_sessies = list()
            bogen_pks_gebruikt_in_sessies = list()
            for sessie in wedstrijd.sessies.all():
                for klasse in sessie.wedstrijdklassen.select_related('boogtype').all():
                    if klasse.pk not in klassen_pks_gebruikt_in_sessies:
                        klassen_pks_gebruikt_in_sessies.append(klasse.pk)
                        if klasse.boogtype.pk not in bogen_pks_gebruikt_in_sessies:
                            bogen_pks_gebruikt_in_sessies.append(klasse.boogtype.pk)
                # for
            # for

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
                        sporter = account.sporter_set.all()[0]
                        wedstrijd.voorwaarden_a_status_who = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())
                        wedstrijd.voorwaarden_a_status_when = timezone.now()
                        wedstrijd.voorwaarden_a_status_acceptatie = True

                    if wedstrijd.voorwaarden_a_status_acceptatie:
                        wedstrijd.wa_status = WEDSTRIJD_WA_STATUS_A

                aantal_banen = request.POST.get('aantal_banen', str(wedstrijd.aantal_banen))
                try:
                    aantal_banen = int(aantal_banen[:5])        # afkappen voor de veiligheid
                except ValueError:
                    raise Http404('Fout in aantal banen')

                if 1 <= aantal_banen <= 100:
                    wedstrijd.aantal_banen = aantal_banen

                wedstrijd.scheidsrechters = request.POST.get('scheidsrechters', wedstrijd.scheidsrechters)[:500]

            if not block_edits:
                begrenzing = request.POST.get('begrenzing', '')[:20]     # afkappen voor de veiligheid
                for code in WEDSTRIJD_BEGRENZING_TO_STR.keys():
                    if begrenzing == 'begrenzing_%s' % code:
                        wedstrijd.begrenzing = code
                        break
                # for

                boog_pks = list()
                for boog in BoogType.objects.all():
                    if boog.pk in bogen_pks_gebruikt_in_sessies or request.POST.get('boog_%s' % boog.afkorting, ''):
                        # deze boog is gekozen
                        boog_pks.append(boog.pk)
                # for
                wedstrijd.boogtypen.set(boog_pks)

                wedstrijd.contact_naam = request.POST.get('contact_naam', wedstrijd.contact_naam)[:50]
                wedstrijd.contact_email = request.POST.get('contact_email', wedstrijd.contact_email)[:150]
                wedstrijd.contact_website = request.POST.get('contact_website', wedstrijd.contact_website)[:100]
                wedstrijd.contact_telefoon = request.POST.get('contact_telefoon', wedstrijd.contact_telefoon)[:50]

                wedstrijd.bijzonderheden = request.POST.get('bijzonderheden', '')[:1000]

            data = request.POST.get('locatie', '')
            if data:
                for locatie in (wedstrijd
                                .organiserende_vereniging
                                .wedstrijdlocatie_set
                                .exclude(zichtbaar=False)):
                    sel = 'loc_%s' % locatie.pk
                    if sel == data:
                        wedstrijd.locatie = locatie
                        break   # from the for
                # for

            aanwezig = request.POST.get('aanwezig', '')     # bevat 'aanwezig_NN'
            if aanwezig.startswith('aanwezig_'):
                for mins in (10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60):
                    sel = 'aanwezig_%d' % mins
                    if aanwezig == sel:
                        wedstrijd.minuten_voor_begin_sessie_aanwezig_zijn = mins
                        break       # from the for
                # for

            if request.POST.get('extern', ''):
                wedstrijd.extern_beheerd = True
            else:
                wedstrijd.extern_beheerd = False

            wedstrijd.save()

            boog_pks = list(wedstrijd.boogtypen.values_list('pk', flat=True))
            gekozen_klassen = list()
            for klasse in (KalenderWedstrijdklasse
                           .objects
                           .exclude(buiten_gebruik=True)
                           .select_related('boogtype')
                           .order_by('volgorde')):

                if klasse.pk in klassen_pks_gebruikt_in_sessies or request.POST.get('klasse_%s' % klasse.pk, ''):
                    # klasse is gewenst
                    if klasse.boogtype.pk in boog_pks:
                        # klasse boogtype is nog steeds gewenst
                        gekozen_klassen.append(klasse)
            # for

            # werk de manytomany koppelingen bij
            wedstrijd.wedstrijdklassen.set(gekozen_klassen)

            self._verplaats_sessies(wedstrijd, oude_datum_begin)

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
            wedstrijd_pk = int(str(kwargs['wedstrijd_pk'])[:6])     # afkappen voor de veiligheid
            wedstrijd = (KalenderWedstrijd
                         .objects
                         .get(pk=wedstrijd_pk))
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
                wedstrijd.save(update_fields=['status'])
                # maak een taak aan voor de BB
                self._maak_taak_voor_bb(wedstrijd, 'Wedstrijd %s is ingediend voor goedkeuring')

        else:
            next_url = reverse('Kalender:manager')

            if annuleer:
                # annuleer deze wedstrijd
                wedstrijd.status = WEDSTRIJD_STATUS_GEANNULEERD
                wedstrijd.save(update_fields=['status'])

                # maak een taak aan voor de HWL
                self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geannuleerd")

            elif wedstrijd.status == WEDSTRIJD_STATUS_ONTWERP:
                if verder:
                    wedstrijd.status = WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING
                    wedstrijd.save(update_fields=['status'])

            elif wedstrijd.status == WEDSTRIJD_STATUS_WACHT_OP_GOEDKEURING:
                if terug:
                    # afgekeurd --> terug naar ontwerp
                    wedstrijd.status = WEDSTRIJD_STATUS_ONTWERP
                    wedstrijd.save(update_fields=['status'])

                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is terug gezet naar de status 'ontwerp'")

                elif verder:
                    # goedgekeurd --> naar geaccepteerd
                    wedstrijd.status = WEDSTRIJD_STATUS_GEACCEPTEERD
                    wedstrijd.save(update_fields=['status'])

                    # maak een taak aan voor de HWL
                    self._maak_taak_voor_hwl(wedstrijd, "Wedstrijd %s is nu geaccepteerd en openbaar")

        return HttpResponseRedirect(next_url)

# end of file
