# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.utils.timezone import localtime
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.definities import (BESTELLING_STATUS2STR, BESTELLING_STATUS_BETALING_ACTIEF,
                                   BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_MISLUKT,
                                   BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_TRANSPORT_OPHALEN,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD,
                                   BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING,
                                   BESTELLING_KORT_BREAK)
from Bestelling.models import Bestelling
from Bestelling.operations import bestel_mutatieverzoek_annuleer
from Bestelling.plugins.alle_bestel_plugins import wedstrijd_bestel_plugin
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT, TRANSACTIE_TYPE_HANDMATIG
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.models import Functie
from Functie.rol import rol_get_huidige
from decimal import Decimal

TEMPLATE_TOON_BESTELLINGEN = 'bestelling/toon-bestellingen.dtl'
TEMPLATE_BESTELLING_DETAILS = 'bestelling/toon-bestelling-details.dtl'


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
        return self.rol_nu != Rol.ROL_NONE

    @staticmethod
    def _get_bestellingen(account, context):

        context['bestellingen'] = bestellingen = (Bestelling
                                                  .objects
                                                  .filter(account=account)
                                                  .prefetch_related('regels')
                                                  .order_by('-aangemaakt'))     # nieuwste eerst

        for bestelling in bestellingen:

            regels = (bestelling
                      .regels
                      .exclude(code=BESTELLING_REGEL_CODE_WEDSTRIJD_KORTING)
                      .order_by('code', 'pk'))

            bestelling.beschrijving = [regel.korte_beschrijving.split(BESTELLING_KORT_BREAK)[0]
                                       for regel in regels]

            status = bestelling.status
            if status == BESTELLING_STATUS_NIEUW:
                # nieuw is een interne state. Na een verlopen/mislukte betalen wordt deze status ook gezet.
                # toon daarom als "te betalen"
                status = BESTELLING_STATUS_BETALING_ACTIEF

            if status == BESTELLING_STATUS_BETALING_ACTIEF:
                bestelling.status_str = 'Te betalen'
            else:
                bestelling.status_str = BESTELLING_STATUS2STR[status]

            bestelling.status_aandacht = status in (BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_MISLUKT)

            bestelling.url_details = reverse('Bestelling:toon-bestelling-details',
                                             kwargs={'bestel_nr': bestelling.bestel_nr})
        # for

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        account = get_account(self.request)

        self._get_bestellingen(account, context)

        # contactgegevens voor hulpvragen
        functie = Functie.objects.filter(rol='MWW').first()
        if functie:
            context['email_webshop'] = functie.bevestigde_email

        functie = Functie.objects.filter(rol='MO').first()
        if functie:
            context['email_opleidingen'] = functie.bevestigde_email

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
        return self.rol_nu != Rol.ROL_NONE

    @staticmethod
    def _beschrijf_inhoud_bestelling(bestelling: Bestelling):
        """ beschrijf de inhoud van een bestelling """

        controleer_euro = Decimal(0)

        regels = (bestelling
                  .regels
                  .order_by('code', 'pk'))       # geen schoonheidsprijs, maar wel vaste volgorde

        regel_nr = 0
        for regel in regels:
            regel_nr += 1
            regel.regel_nr = regel_nr
            regel.korte_beschrijving = regel.korte_beschrijving.replace(BESTELLING_KORT_BREAK, '\n')
            regel.korting_redenen = regel.korting_redenen.replace(BESTELLING_KORT_BREAK, '\n')
            regel.bedrag_euro_str = format_bedrag_euro(regel.bedrag_euro)
            controleer_euro += regel.bedrag_euro
        # for

        # nooit een negatief totaalbedrag tonen want we geven geen geld weg
        if controleer_euro < 0:
            controleer_euro = Decimal(0)

        bevat_fout = controleer_euro != bestelling.totaal_euro

        return regels, bevat_fout

    @staticmethod
    def _beschrijf_transacties(bestelling) -> (list, Decimal):
        transacties = list()
        totaal_euro = Decimal(0)

        transactie_mollie = None
        for transactie in bestelling.transacties.order_by('when'):  # oudste eerst
            transactie.stamp_str = localtime(transactie.when).strftime('%Y-%m-%d %H:%M')

            if transactie.transactie_type == TRANSACTIE_TYPE_HANDMATIG:
                transactie.type_str = 'Overboeking'
                transacties.append(transactie)
                transactie.regels = regels = list()
                tup = ('Ontvangen', format_bedrag_euro(transactie.bedrag_handmatig))
                transactie.regels.append(tup)
                totaal_euro += transactie.bedrag_handmatig

            if transactie.transactie_type == TRANSACTIE_TYPE_MOLLIE_PAYMENT:
                # onthoudt de nieuwste - output is verderop
                transactie_mollie = transactie
        # for

        # voeg stand van zaken van Mollie Payment toe
        if transactie_mollie:
            transactie_mollie.type_str = 'Mollie'
            transactie_mollie.regels = regels = list()

            if transactie_mollie.payment_status in ('canceled', 'cancelled', 'expired', 'failed'):
                tup = ('Niet gelukt', None)
                regels.append(tup)
            else:
                tup = (transactie_mollie.beschrijving, None)    # voorbeeld: MH-1001111 MijnHandboogsport
                regels.append(tup)

                if transactie_mollie.klant_naam:
                    tup = ('Ontvangen van %s' % transactie_mollie.klant_naam, None)
                    regels.append(tup)

                if transactie_mollie.bedrag_terugbetaald:
                    tup = ('Betaald (resterend)', format_bedrag_euro(transactie_mollie.bedrag_beschikbaar))
                    regels.append(tup)
                    totaal_euro += transactie_mollie.bedrag_beschikbaar

                    tup = ('Terugbetaald', format_bedrag_euro(transactie_mollie.bedrag_terugbetaald))
                    regels.append(tup)
                    totaal_euro -= transactie_mollie.bedrag_terugbetaald
                else:
                    tup = ('Betaald', format_bedrag_euro(transactie_mollie.bedrag_beschikbaar))
                    regels.append(tup)
                    totaal_euro += transactie_mollie.bedrag_beschikbaar

                # if transactie_mollie.bedrag_teruggevorderd:
                #     tup = ('Teruggevorderd',  format_bedrag_euro(transactie_mollie.bedrag_teruggevorderd))
                #     regels.append(tup)
                #     totaal_euro -= transactie_mollie.bedrag_teruggevorderd

            transacties.append(transactie_mollie)

        return transacties, totaal_euro

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

        context['regels'], context['bevat_fout'] = self._beschrijf_inhoud_bestelling(bestelling)

        context['transacties'], transacties_euro = self._beschrijf_transacties(bestelling)

        if bestelling.status == BESTELLING_STATUS_GEANNULEERD:
            context['is_geannuleerd'] = True
        else:
            context['transport_ophalen'] = (bestelling.transport == BESTELLING_TRANSPORT_OPHALEN)

            if bestelling.status == BESTELLING_STATUS_AFGEROND:
                # geen betaling meer nodig
                pass
            else:
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
                        context['url_afrekenen'] = reverse('Bestelling:bestelling-afrekenen',
                                                           kwargs={'bestel_nr': bestelling.bestel_nr})

                if bestelling.status in (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_BETALING_ACTIEF):
                    context['url_annuleren'] = reverse('Bestelling:annuleer-bestelling',
                                                       kwargs={'bestel_nr': bestelling.bestel_nr})

        # zoek de kwalificatiescores erbij
        kwalificatie_scores = list()
        for regel in bestelling.regels.filter(code=BESTELLING_REGEL_CODE_WEDSTRIJD):
            wedstrijd = wedstrijd_bestel_plugin.wil_kwalificatiescores(regel)
            if wedstrijd:
                kwalificatie_scores.append(wedstrijd)
        # for
        context['toon_kwalificatie_scores'] = len(kwalificatie_scores) > 0
        context['kwalificatie_scores'] = kwalificatie_scores

        context['url_voorwaarden_wedstrijden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL
        context['url_voorwaarden_opleidingen'] = settings.VERKOOPVOORWAARDEN_OPLEIDINGEN_URL
        context['url_voorwaarden_webwinkel'] = settings.VERKOOPVOORWAARDEN_WEBWINKEL_URL

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (reverse('Bestelling:toon-bestellingen'), 'Bestellingen'),
            (None, 'Bestelling'),
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
        return rol_nu != Rol.ROL_NONE            # inlog vereist

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
        url = reverse('Bestelling:toon-bestellingen')
        return HttpResponseRedirect(url)


# end of file
