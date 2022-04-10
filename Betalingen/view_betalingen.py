# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import Account
from Functie.rol import Rollen, rol_get_huidige_functie
from Taken.taken import maak_taak
from .models import BetalingenActieveTransacties, MOLLIE_PAYMENT_ID_MAXLENGTH
import datetime

TEMPLATE_KALENDER_WIJZIG_WEDSTRIJD = 'kalender/wijzig-wedstrijd.dtl'


class MollieWebhookView(View):

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen om de POST request af te handelen.
            Dit wordt gebruikt als Webhook om status changes van Mollie te ontvangen.
        """

        data = request.POST.get('id', '')[:MOLLIE_PAYMENT_ID_MAXLENGTH]     # afkappen voor de veiligheid

        # filter rare tekens eruit
        payment_id = ''
        for char in data:
            if char.isalnum():
                payment_id += char
        # for

        if not BetalingenActieveTransacties.objects.filter(payment_id=payment_id).count() > 0:
            raise Http404('Onbekend')



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

            disc2str = ORGANISATIE_WEDSTRIJD_DISCIPLINE_STRS[wedstrijd.organisatie]

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
                for afk in disc2str.keys():
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

        # FUTURE: zet wijzigingen in het logboek, of begin een logboekje per wedstrijd

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
