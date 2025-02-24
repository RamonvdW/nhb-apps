# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Betaal.format import format_bedrag_euro
from Bestelling.definities import BESTELLING_TRANSPORT_VERZEND, BESTELLING_TRANSPORT_OPHALEN
from Bestelling.models import BestellingMandje
from Bestelling.operations.mandje import mandje_tel_inhoud
from Bestelling.operations.mutaties import (bestel_mutatieverzoek_maak_bestellingen,
                                            bestel_mutatieverzoek_verwijder_product_uit_mandje)
from Betaal.models import BetaalInstellingenVereniging
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Sporter.models import get_sporter
from Vereniging.models import Vereniging
from decimal import Decimal


TEMPLATE_MANDJE_TOON_INHOUD = 'bestelling/toon-mandje.dtl'


class ToonInhoudMandje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de inhoud van zijn mandje zien """

    # class variables shared by all instances
    template_name = TEMPLATE_MANDJE_TOON_INHOUD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """

        if request.user.is_authenticated:
            account = get_account(request)
            if account.is_gast:
                gast = account.gastregistratie_set.first()
                if gast and gast.fase != REGISTRATIE_FASE_COMPLEET:
                    # registratie is nog niet voltooid
                    # dwing terug naar de lijst met vragen
                    return redirect('Registreer:gast-meer-vragen')

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _beschrijf_inhoud_mandje(account):
        """ beschrijf de producten die in het mandje liggen """

        mandje_is_leeg = True
        bevat_fout = False

        ontvanger2product_pks = dict()      # [ver_nr] = [product.pk, ...]
        ver_nr2instellingen = dict()        # [ver_nr] = BetaalInstellingenVereniging

        for instellingen in BetaalInstellingenVereniging.objects.select_related('vereniging').all():
            ver_nr = instellingen.vereniging.ver_nr
            ver_nr2instellingen[ver_nr] = instellingen
        # for

        try:
            instellingen_bond = ver_nr2instellingen[settings.BETAAL_VIA_BOND_VER_NR]
        except KeyError:
            # nog niet aangemaakt
            instellingen_bond = None

        try:
            mandje = BestellingMandje.objects.prefetch_related('producten').get(account=account)
        except BestellingMandje.DoesNotExist:
            # geen mandje
            mandje = None
            producten = None
        else:
            controleer_euro = Decimal(0)

            regels = mandje.regels.order_by('pk')       # volgorde waarop ze in het mandje gelegd zijn

            # producten = (mandje
            #              .producten
            #              .select_related('wedstrijd_inschrijving',
            #                              'wedstrijd_inschrijving__wedstrijd',
            #                              'wedstrijd_inschrijving__wedstrijd__locatie',
            #                              'wedstrijd_inschrijving__wedstrijd__organiserende_vereniging',
            #                              'wedstrijd_inschrijving__wedstrijdklasse',
            #                              'wedstrijd_inschrijving__sessie',
            #                              'wedstrijd_inschrijving__sporterboog',
            #                              'wedstrijd_inschrijving__sporterboog__boogtype',
            #                              'wedstrijd_inschrijving__sporterboog__sporter',
            #                              'wedstrijd_inschrijving__sporterboog__sporter__bij_vereniging',
            #                              'evenement_inschrijving',
            #                              'evenement_inschrijving__evenement__organiserende_vereniging',
            #                              'evenement_inschrijving__koper',
            #                              'evenement_inschrijving__sporter',
            #                              'evenement_inschrijving__sporter__bij_vereniging',
            #                              'opleiding_inschrijving',
            #                              'opleiding_inschrijving__opleiding',
            #                              'webwinkel_keuze',
            #                              'webwinkel_keuze__product')
            #              .order_by('pk'))       # volgorde waarop ze in het mandje gelegd zijn

            for regel in regels:
                mandje_is_leeg = False

                controleer_euro += regel.prijs_euro
                controleer_euro -= regel.korting_euro

                regel.prijs_euro_str = format_bedrag_euro(regel.prijs_euro)
                regel.korting_euro_str = format_bedrag_euro(regel.korting_euro)

                # maak een knop om deze bestelling te verwijderen uit het mandje
                regel.url_verwijder = reverse('Bestelling:mandje-verwijder-product',
                                              kwargs={'product_pk': regel.pk})
            # for

            if False:
                for product in producten:

                    product.gebruikte_korting_str = None
                    product.combi_reden = list()
                    product.is_combi_korting = False
                    product.kan_afrekenen = False

                    if product.wedstrijd_inschrijving:
                        product.gebruikte_korting_str, product.combi_reden = wedstrijd_beschrijf_korting(product)
                        product.is_combi_korting = len(product.combi_reden) > 0
                        product.kan_afrekenen = True

                        ver_nr = product.wedstrijd_inschrijving.wedstrijd.organiserende_vereniging.ver_nr
                        try:
                            instellingen = ver_nr2instellingen[ver_nr]
                        except KeyError:
                            # geen instellingen, dus kan geen betaling ontvangen
                            product.kan_afrekenen = False
                        else:
                            if instellingen.akkoord_via_bond:
                                ver_nr = settings.BETAAL_VIA_BOND_VER_NR
                                if instellingen_bond is None or instellingen_bond.mollie_api_key == '':
                                    product.kan_afrekenen = False

                        try:
                            ontvanger2product_pks[ver_nr].append(product.pk)
                        except KeyError:
                            ontvanger2product_pks[ver_nr] = [product.pk]

                    elif product.evenement_inschrijving:
                        pass

                    elif product.opleiding_inschrijving:
                        pass

                    elif product.webwinkel_keuze:
                        # FUTURE: kortingen
                        pass

                    else:
                        tup = ('Fout', 'Onbekend product')
                        product.beschrijving.append(tup)
                        bevat_fout = True
                        product.kan_afrekenen = False

                    if product.korting_euro and not product.gebruikte_korting_str:
                        # print('Onverwacht: product %s (pk=%s) heeft korting %s' % (
                        #           product, product.pk, product.korting_euro))
                        product.gebruikte_korting_str = "Onbekende korting"
                        bevat_fout = True

                    controleer_euro += product.prijs_euro
                    controleer_euro -= product.korting_euro

                    # maak een knop om deze bestelling te verwijderen uit het mandje
                    product.url_verwijder = reverse('Bestelling:mandje-verwijder-product',
                                                    kwargs={'product_pk': product.pk})

                    mandje_is_leeg = False
                # for

            # nooit een negatief totaalbedrag tonen want we geven geen geld weg
            if controleer_euro < 0:
                controleer_euro = Decimal(0)

            controleer_euro += mandje.verzendkosten_euro

            if controleer_euro != mandje.totaal_euro:
                bevat_fout = True

        return mandje, regels, ontvanger2product_pks, mandje_is_leeg, bevat_fout

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = get_account(self.request)

        # omdat het heel raar is als het tellertje op het mandje niet overeenkomt
        # met de inhoud van het mandje, forceren we de telling hier nog een keer
        mandje_tel_inhoud(self.request, account)
        # eval_mandje_inhoud(self.request)

        # force dat het mandje icoon getoond wordt
        context['menu_toon_mandje'] = True

        mandje, regels, ontvanger2product_pks, mandje_is_leeg, bevat_fout = self._beschrijf_inhoud_mandje(account)

        toon_transport = False
        if mandje:
            if mandje.transport == BESTELLING_TRANSPORT_OPHALEN:
                toon_transport = True
                context['ophalen_ver'] = Vereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)

            elif mandje.transport == BESTELLING_TRANSPORT_VERZEND:
                toon_transport = settings.WEBWINKEL_TRANSPORT_OPHALEN_MAG
                sporter = get_sporter(account)
                context['koper_sporter'] = sporter

        geen_afleveradres = toon_transport
        if toon_transport and not mandje_is_leeg:
            if account.is_gast:
                # geef gastaccounts mogelijkheid om afleveradres in te voeren
                toon_transport = False
                context['url_afleveradres'] = reverse('Bestelling:wijzig-afleveradres')
            else:
                # volwaardig lid: afleveradres automatisch invullen
                sporter = get_sporter(account)
                mandje.afleveradres_regel_1 = sporter.postadres_1
                mandje.afleveradres_regel_2 = sporter.postadres_2
                mandje.afleveradres_regel_3 = sporter.postadres_3

            for nr in (1, 2, 3, 4, 5):
                regel_str = 'afleveradres_regel_%s' % nr
                regel = getattr(mandje, regel_str)
                if regel:
                    geen_afleveradres = False
                    break       # from the for
            # for

        context['geen_afleveradres'] = geen_afleveradres
        context['toon_transport'] = toon_transport
        context['mandje_is_leeg'] = mandje_is_leeg
        context['mandje'] = mandje
        #context['producten'] = producten
        context['regels'] = regels
        context['bevat_fout'] = bevat_fout
        #context['aantal_betalingen'] = len(ontvanger2product_pks.keys())
        context['url_kies_transport'] = reverse('Bestelling:kies-transport')
        context['url_voorwaarden_webwinkel'] = settings.VERKOOPVOORWAARDEN_WEBWINKEL_URL
        context['url_voorwaarden_wedstrijden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL
        context['url_voorwaarden_opleidingen'] = settings.VERKOOPVOORWAARDEN_OPLEIDINGEN_URL

        if not (bevat_fout or mandje_is_leeg or geen_afleveradres):
            context['url_bestellen'] = reverse('Bestelling:toon-inhoud-mandje')

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de koper op de knop BESTELLING AFRONDEN gedrukt heeft
            Hier converteren we het mandje in een bevroren bestelling die afgerekend kan worden.
        """

        snel = str(request.POST.get('snel', ''))[:1]

        account = get_account(self.request)

        try:
            mandje = BestellingMandje.objects.prefetch_related('producten').get(account=account)
        except BestellingMandje.DoesNotExist:
            # geen mandje
            raise Http404('Mandje niet gevonden')

        # nu kunnen we het afleveradres permanent maken, ook voor leden

        if mandje.transport == BESTELLING_TRANSPORT_VERZEND:
            if not account.is_gast:
                # volwaardig lid: afleveradres automatisch invullen
                sporter = get_sporter(account)
                mandje.afleveradres_regel_1 = sporter.postadres_1
                mandje.afleveradres_regel_2 = sporter.postadres_2
                mandje.afleveradres_regel_3 = sporter.postadres_3

            geen_afleveradres = True
            for nr in (1, 2, 3, 4, 5):
                regel_str = 'afleveradres_regel_%s' % nr
                regel = getattr(mandje, regel_str)
                if regel:
                    geen_afleveradres = False
                    break       # from the for
            # for

            if geen_afleveradres:
                raise Http404('Afleveradres onbekend')

        mandje.save(update_fields=['afleveradres_regel_1', 'afleveradres_regel_2', 'afleveradres_regel_3',
                                   'afleveradres_regel_4', 'afleveradres_regel_5'])

        bestel_mutatieverzoek_maak_bestellingen(account, snel == '1')
        # achtergrondtaak zet het mandje om in bestellingen

        # zorg dat de knop het juiste aantal toont
        mandje_tel_inhoud(request, account)

        # ga naar de pagina met alle bestellingen, zodat de betaling gestart kan worden
        url = reverse('Bestelling:toon-bestellingen')
        return HttpResponseRedirect(url)


class VerwijderProductUitMandje(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE

    def post(self, request, *args, **kwargs):

        snel = str(request.POST.get('snel', ''))[:1]

        try:
            product_pk = str(kwargs['product_pk'])[:6]        # afkappen voor de veiligheid
            product_pk = int(product_pk)
        except (KeyError, ValueError, TypeError):
            raise Http404('Verkeerde parameter')

        # zoek de regel op in het mandje van de ingelogde gebruiker
        account = get_account(request)
        try:
            mandje = BestellingMandje.objects.prefetch_related('producten').get(account=account)
        except BestellingMandje.DoesNotExist:
            raise Http404('Niet gevonden')
        else:
            qset = mandje.producten.filter(pk=product_pk)
            if qset.exists():
                # product zit in het mandje
                product = qset[0]

                bestel_mutatieverzoek_verwijder_product_uit_mandje(account, product, snel == '1')
                # achtergrondtaak geeft dit door aan de kalender/opleiding

                mandje_tel_inhoud(self.request, account)
            else:
                raise Http404('Niet gevonden in jouw mandje')

        url = reverse('Bestelling:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


# end of file
