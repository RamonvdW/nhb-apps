# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.utils.timezone import localtime
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestel.definities import (BESTELLING_STATUS2STR, BESTELLING_STATUS_BETALING_ACTIEF,
                               BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_MISLUKT,
                               BESTELLING_STATUS_GEANNULEERD,
                               BESTEL_TRANSPORT_OPHALEN)
from Bestel.models import Bestelling
from Bestel.plugins.product_info import beschrijf_product, beschrijf_korting
from Bestel.operations.mutaties import bestel_mutatieverzoek_annuleer
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Functie.definities import Rollen
from Functie.models import Functie
from Functie.rol import rol_get_huidige
from Kalender.view_maand import maak_compacte_wanneer_str
from decimal import Decimal


TEMPLATE_TOON_BESTELLINGEN = 'bestel/toon-bestellingen.dtl'
TEMPLATE_BESTELLING_DETAILS = 'bestel/toon-bestelling-details.dtl'
TEMPLATE_BESTELLING_AFREKENEN = 'bestel/bestelling-afrekenen.dtl'
TEMPLATE_BESTELLING_AFGEROND = 'bestel/bestelling-afgerond.dtl'


class ToonBestellingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker zijn eigen bestellingen terug zien en een betaling opstarten """

    # class variables shared by all instances
    template_name = TEMPLATE_TOON_BESTELLINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    @staticmethod
    def _get_bestellingen(account, context):

        context['bestellingen'] = bestellingen = (Bestelling
                                                  .objects
                                                  .filter(account=account)
                                                  .prefetch_related('producten')
                                                  .order_by('-aangemaakt'))     # nieuwste eerst

        for bestelling in bestellingen:

            bestelling.beschrijving = beschrijving = list()

            for product in (bestelling
                            .producten
                            .select_related('wedstrijd_inschrijving',
                                            'wedstrijd_inschrijving__wedstrijd',
                                            'wedstrijd_inschrijving__sporterboog__sporter')):

                if product.wedstrijd_inschrijving:
                    beschrijving.append(product.wedstrijd_inschrijving.korte_beschrijving())
                elif product.evenement_inschrijving:
                    beschrijving.append(product.evenement_inschrijving.korte_beschrijving())
                elif product.webwinkel_keuze:
                    beschrijving.append(product.webwinkel_keuze.product.omslag_titel)
                else:
                    beschrijving.append("??")
            # for

            status = bestelling.status
            if status == BESTELLING_STATUS_NIEUW:
                # nieuw is een interne state. Na een verlopen/mislukte betalen wordt deze status ook gezet.
                # toon daarom als "te betalen"
                status = BESTELLING_STATUS_BETALING_ACTIEF

            bestelling.status_str = BESTELLING_STATUS2STR[status]
            bestelling.status_aandacht = (status == BESTELLING_STATUS_BETALING_ACTIEF)

            bestelling.url_details = reverse('Bestel:toon-bestelling-details',
                                             kwargs={'bestel_nr': bestelling.bestel_nr})
        # for

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)

        self._get_bestellingen(account, context)

        # contactgegevens voor hulpvragen
        functie = Functie.objects.filter(rol='MWW')[0]
        context['email_webshop'] = functie.bevestigde_email
        context['email_support'] = settings.EMAIL_SUPPORT

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Bestellingen'),
        )

        return context


class ToonBestellingDetailsView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de details van een bestelling inzien en een betaling opstarten """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_DETAILS
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    @staticmethod
    def _beschrijf_inhoud_bestelling(bestelling: Bestelling):
        """ beschrijf de inhoud van een bestelling """

        bevat_fout = False

        controleer_euro = Decimal(0)

        producten = (bestelling
                     .producten
                     .select_related('wedstrijd_inschrijving',
                                     'wedstrijd_inschrijving__wedstrijd',
                                     'wedstrijd_inschrijving__wedstrijd__locatie',
                                     'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging',
                                     'wedstrijd_inschrijving__wedstrijdklasse',
                                     'wedstrijd_inschrijving__sessie',
                                     'wedstrijd_inschrijving__sporterboog',
                                     'wedstrijd_inschrijving__sporterboog__boogtype',
                                     'wedstrijd_inschrijving__sporterboog__sporter',
                                     'wedstrijd_inschrijving__sporterboog__sporter__bij_vereniging',
                                     'evenement_inschrijving',
                                     'evenement_inschrijving__evenement__organiserende_vereniging',
                                     'evenement_inschrijving__koper',
                                     'evenement_inschrijving__sporter',
                                     'evenement_inschrijving__sporter__bij_vereniging',
                                     'webwinkel_keuze',
                                     'webwinkel_keuze__product')
                     .order_by('pk'))       # geen schoonheidsprijs, maar wel vaste volgorde

        for product in producten:
            # maak een beschrijving van deze regel
            product.beschrijving = beschrijf_product(product)

            product.gebruikte_korting_str, product.combi_reden = beschrijf_korting(product)
            product.is_combi_korting = len(product.combi_reden) > 0

            if product.wedstrijd_inschrijving:
                pass

            elif product.evenement_inschrijving:
                pass

            elif product.webwinkel_keuze:
                pass

            else:
                tup = ('Fout', 'Onbekend product')
                product.beschrijving.append(tup)
                bevat_fout = True

            controleer_euro += product.prijs_euro
            controleer_euro -= product.korting_euro
        # for

        # nooit een negatief totaalbedrag tonen want we geven geen geld weg
        if controleer_euro < 0:
            controleer_euro = Decimal(0)

        controleer_euro += bestelling.verzendkosten_euro

        if controleer_euro != bestelling.totaal_euro:
            bevat_fout = True

        return producten, bevat_fout

    @staticmethod
    def _beschrijf_transacties(bestelling):

        transacties_euro = Decimal(0)

        transacties = (bestelling
                       .transacties
                       .all())

        for transactie in transacties:
            transactie.regels = regels = list()

            regel = localtime(transactie.when).strftime('%Y-%m-%d %H:%M')
            regels.append(regel)

            regels.append(transactie.beschrijving)

            if transactie.is_restitutie:
                regels.append('Restitutie')
                transacties_euro -= transactie.bedrag_euro_klant
            else:
                if transactie.klant_naam:
                    regels.append('Ontvangen van %s' % transactie.klant_naam)
                transacties_euro += transactie.bedrag_euro_klant
        # for

        return transacties, transacties_euro

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        context['bestelling'] = bestelling

        context['transacties'], transacties_euro = self._beschrijf_transacties(bestelling)

        if bestelling.status == BESTELLING_STATUS_GEANNULEERD:
            context['is_geannuleerd'] = True
        else:
            context['transport_ophalen'] = (bestelling.transport == BESTEL_TRANSPORT_OPHALEN)

            rest_euro = bestelling.totaal_euro - transacties_euro
            if rest_euro > 0:
                context['rest_euro'] = rest_euro

            if rest_euro >= Decimal('0.01'):
                # betaling is vereist

                if bestelling.ontvanger.moet_handmatig():
                    # betaling moet handmatig
                    context['moet_handmatig'] = True
                else:
                    # betaling gaat via Mollie
                    context['url_afrekenen'] = reverse('Bestel:bestelling-afrekenen',
                                                       kwargs={'bestel_nr': bestelling.bestel_nr})

            if bestelling.status in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF):
                context['url_annuleren'] = reverse('Bestel:annuleer-bestelling',
                                                   kwargs={'bestel_nr': bestelling.bestel_nr})

        kwalificatie_scores = list()
        for product in (bestelling
                        .producten
                        .exclude(wedstrijd_inschrijving=None)
                        .select_related('wedstrijd_inschrijving',
                                        'wedstrijd_inschrijving__wedstrijd',
                                        'wedstrijd_inschrijving__wedstrijd__locatie',
                                        'wedstrijd_inschrijving__sporterboog__sporter',)
                        .all()):
            inschrijving = product.wedstrijd_inschrijving
            wedstrijd = inschrijving.wedstrijd
            if wedstrijd.eis_kwalificatie_scores:       # TODO: einddatum voor wijzigingen
                wedstrijd.url_kwalificatie_scores = reverse('WedstrijdInschrijven:inschrijven-kwalificatie-scores',
                                                            kwargs={'inschrijving_pk': inschrijving.pk})
                wedstrijd.datum_str = maak_compacte_wanneer_str(wedstrijd.datum_begin, wedstrijd.datum_einde)
                wedstrijd.plaats_str = wedstrijd.locatie.plaats
                wedstrijd.sporter_str = inschrijving.sporterboog.sporter.lid_nr_en_volledige_naam()
                kwalificatie_scores.append(wedstrijd)
        # for
        context['toon_kwalificatie_scores'] = len(kwalificatie_scores) > 0
        context['kwalificatie_scores'] = kwalificatie_scores

        context['url_voorwaarden_wedstrijden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL
        context['url_voorwaarden_webwinkel'] = settings.VERKOOPVOORWAARDEN_WEBWINKEL_URL

        context['producten'], context['bevat_fout'] = self._beschrijf_inhoud_bestelling(bestelling)

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestel:toon-bestellingen'), 'Bestellingen'),
            (None, 'Bestelling'),
        )

        return context


class BestellingAfrekenenView(UserPassesTestMixin, TemplateView):

    """ Deze functie wordt gebruikt om een betaling op te starten.
        Als de betaling nog niet bestaat, dan wordt deze opgestart via de POST.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_AFREKENEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None      # wordt gezet door dispatch()
        self.bestelling = None  # wordt gezet door dispatch()

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.rol_nu not in (Rollen.ROL_NONE, None)

    def dispatch(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen voor get_queryset/get_context_data
            hier is het mogelijk om een redirect te doen.

            Let op: test_func is nog niet aangeroepen
        """
        self.rol_nu = rol_get_huidige(self.request)

        if self.rol_nu != Rollen.ROL_NONE:

            account = get_account(self.request)

            try:
                bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
                bestel_nr = int(bestel_nr)
                bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
            except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
                raise Http404('Niet gevonden')

            if bestelling.status == BESTELLING_STATUS_AFGEROND:
                # betaling is al klaar
                url = reverse('Bestel:na-de-betaling', kwargs={'bestel_nr': bestelling.bestel_nr})
                return HttpResponseRedirect(url)

            self.bestelling = bestelling

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # de details worden via DynamicBestellingCheckStatus opgehaald
        context['bestelling'] = bestelling = self.bestelling

        context['url_status_check'] = reverse('Bestel:dynamic-check-status', kwargs={'bestel_nr': bestelling.bestel_nr})

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestel:toon-bestellingen'), 'Bestellingen'),
            (reverse('Bestel:toon-bestelling-details', kwargs={'bestel_nr': bestelling.bestel_nr}), 'Bestelling'),
            (None, 'Afrekenen')
        )

        return context

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de gebruiker op de knop BETALEN drukt in de bestelling
            de enige taak van deze functie is een bestelling met status MISLUKT terug zetten naar NIEUW.
        """
        if self.bestelling.status == BESTELLING_STATUS_MISLUKT:
            self.bestelling.status = BESTELLING_STATUS_NIEUW
            self.bestelling.save(update_fields=['status'])

        # doorsturen naar de GET
        url = reverse('Bestel:bestelling-afrekenen',
                      kwargs={'bestel_nr': self.bestelling.bestel_nr})
        return HttpResponseRedirect(url)


class DynamicBestellingCheckStatus(UserPassesTestMixin, View):

    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rollen.ROL_NONE

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen vanuit de template om te kijken wat de status van de bestelling/betaling is.

            Dit is een POST by-design, om caching te voorkomen.
        """
        account = get_account(request)

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        # print('bestelling.status=%s' % bestelling.status)
        out = dict()
        out['status'] = 'error'  # fallback

        if bestelling.status == BESTELLING_STATUS_NIEUW:
            # de betaling is nog niet actief
            out['status'] = 'nieuw'

            # start een nieuwe transactie op
            # LET OP: deze tekst moeten we kort houden, want Mollie + iDEAL kapt af op 36 tekens
            #         dus MijnHandboogsport bestelling MH-1234567 verliest de laatste 4 cijfers
            beschrijving = "%s %s" % (bestelling.mh_bestel_nr(), settings.AFSCHRIFT_SITE_NAAM)

            # TODO: is het realistisch dat status NIEUW al transacties heeft?
            rest_euro = bestelling.totaal_euro
            for transactie in bestelling.transacties.all():
                if transactie.is_restitutie:
                    rest_euro += transactie.bedrag_euro_klant
                else:
                    rest_euro -= transactie.bedrag_euro_klant
            # for

            url_betaling_gedaan = settings.SITE_URL + reverse('Bestel:na-de-betaling',
                                                              kwargs={'bestel_nr': bestelling.bestel_nr})

            # start de bestelling via de achtergrond taak
            # deze slaat de referentie naar de mutatie op in de bestelling
            betaal_mutatieverzoek_start_ontvangst(
                        bestelling,
                        beschrijving,
                        rest_euro,
                        url_betaling_gedaan,
                        # snel == '1',
                        snel=True)          # niet wachten op reactie

        elif bestelling.status == BESTELLING_STATUS_BETALING_ACTIEF:
            if bestelling.betaal_mutatie:
                url = bestelling.betaal_mutatie.url_checkout
                if url:
                    # de checkout url is beschikbaar
                    # stuur de bezoeker daar heen
                    out['status'] = 'betaal'
                    out['checkout_url'] = url

        elif bestelling.status == BESTELLING_STATUS_AFGEROND:
            # we zouden hier niet moeten komen
            # TODO: automatisch doorsturen
            out['status'] = 'afgerond'

        elif bestelling.status == BESTELLING_STATUS_MISLUKT:
            out['status'] = 'mislukt'

        else:       # pragma: no cover
            raise Http404('Onbekende status')

        # niet gebruiken: raise Http404('Onbekende status')
        # want een 404 leidt tot een foutmelding pagina met status 200 ("OK")

        return JsonResponse(out)


class BestellingAfgerondView(UserPassesTestMixin, TemplateView):

    """ De CPSP stuurt de gebruiker naar deze view als de betaling afgerond is.
        We checken de status en bedanken de gebruiker of geven instructies voor de vervolgstappen.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_BESTELLING_AFGEROND
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.prefetch_related('transacties').get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        context['bestelling'] = bestelling

        transacties_euro = Decimal(0)
        for transactie in bestelling.transacties.all():
            if transactie.is_restitutie:
                transacties_euro -= transactie.bedrag_euro_klant
            else:
                transacties_euro += transactie.bedrag_euro_klant
        # for

        context['ontvangen'] = transacties_euro

        context['url_afschrift'] = reverse('Bestel:toon-bestelling-details',
                                           kwargs={'bestel_nr': bestelling.bestel_nr})

        context['url_status_check'] = reverse('Bestel:dynamic-check-status',
                                              kwargs={'bestel_nr': bestelling.bestel_nr})

        if bestelling.status == BESTELLING_STATUS_AFGEROND:
            context['is_afgerond'] = True

        elif bestelling.status == BESTELLING_STATUS_BETALING_ACTIEF:
            # hier komen we als de betaling uitgevoerd is, maar de payment-status-changed nog niet
            # binnen is of nog niet verwerkt door de achtergrondtaak.
            # blijf pollen
            context['wacht_op_betaling'] = True

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestel:toon-bestellingen'), 'Bestellingen'),
            (reverse('Bestel:toon-bestelling-details', kwargs={'bestel_nr': bestelling.bestel_nr}), 'Bestelling'),
            (None, 'Status betaling')
        )

        return context


class AnnuleerBestellingView(UserPassesTestMixin, View):

    """ Deze functie wordt gebruikt om een bestelling te annuleren. """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rollen.ROL_NONE            # inlog vereist

    @staticmethod
    def post(request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de gebruiker op de knop ANNULEREN drukt in de bestelling
            de enige taak van deze functie is een bestelling aan te passen naar BESTEL_STATUS_.
        """

        account = get_account(request)
        snel = str(request.POST.get('snel', ''))[:1]

        try:
            bestel_nr = str(kwargs['bestel_nr'])[:7]        # afkappen voor de veiligheid
            bestel_nr = int(bestel_nr)
            bestelling = Bestelling.objects.get(bestel_nr=bestel_nr, account=account)
        except (KeyError, TypeError, ValueError, Bestelling.DoesNotExist):
            raise Http404('Niet gevonden')

        if bestelling.status in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF):
            # verzoek de achtergrondtaak om de annulering te verwerken
            bestel_mutatieverzoek_annuleer(bestelling, snel == '1')

        # redirect naar het bestellingen overzicht
        url = reverse('Bestel:toon-bestellingen')
        return HttpResponseRedirect(url)


# end of file
