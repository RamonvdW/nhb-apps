# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.definities import BESTEL_TRANSPORT_VERZEND, BESTEL_TRANSPORT_OPHALEN
from Bestel.models import BestelMandje
from Bestel.operations.mandje import mandje_tel_inhoud
from Bestel.operations.mutaties import (bestel_mutatieverzoek_maak_bestellingen,
                                        bestel_mutatieverzoek_verwijder_product_uit_mandje)
from Bestel.plugins.product_info import beschrijf_product, beschrijf_korting
from Betaal.models import BetaalInstellingenVereniging
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige
from NhbStructuur.models import NhbVereniging
from Plein.menu import menu_dynamics
from Registreer.definities import REGISTRATIE_FASE_DONE
from decimal import Decimal


TEMPLATE_MANDJE_TOON_INHOUD = 'bestel/toon-mandje.dtl'


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
        return self.rol_nu != Rollen.ROL_NONE

    def dispatch(self, request, *args, **kwargs):
        """ wegsturen als het we geen vragen meer hebben + bij oneigenlijk gebruik """

        if request.user.is_authenticated:
            account = request.user
            if account.is_gast:
                gast = account.gastregistratie_set.first()
                if gast and gast.fase != REGISTRATIE_FASE_DONE:
                    # registratie is nog niet voltooid
                    # dwing terug naar de lijst met vragen
                    return redirect('Registreer:gast-meer-vragen')

        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def _beschrijf_inhoud_mandje(account):
        """ gezamenlijk programma voor het tonen van de inhoud van het mandje en het afrekenen """

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
            mandje = BestelMandje.objects.prefetch_related('producten').get(account=account)
        except BestelMandje.DoesNotExist:
            # geen mandje
            mandje = None
            producten = None
        else:
            controleer_euro = Decimal(0)

            producten = (mandje
                         .producten
                         .select_related('wedstrijd_inschrijving',
                                         'wedstrijd_inschrijving__wedstrijd',
                                         'wedstrijd_inschrijving__sessie',
                                         'wedstrijd_inschrijving__sporterboog',
                                         'wedstrijd_inschrijving__sporterboog__boogtype',
                                         'wedstrijd_inschrijving__sporterboog__sporter',
                                         'webwinkel_keuze',
                                         'webwinkel_keuze__product')
                         .order_by('pk'))       # volgorde waarop ze in het mandje gelegd zijn

            for product in producten:
                # maak een beschrijving van deze regel
                product.beschrijving = beschrijf_product(product)

                product.gebruikte_korting_str, product.combi_reden = beschrijf_korting(product)
                product.is_combi_korting = len(product.combi_reden) > 0
                product.kan_afrekenen = True

                if product.wedstrijd_inschrijving:
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

                elif product.webwinkel_keuze:
                    # TODO: kortingen
                    pass

                else:
                    tup = ('Fout', 'Onbekend product')
                    product.beschrijving.append(tup)
                    bevat_fout = True
                    product.kan_afrekenen = False

                if product.korting_euro and not product.gebruikte_korting_str:
                    # print('Onverwacht: product %s (pk=%s) heeft korting %s' % (product, product.pk, product.korting_euro))
                    product.gebruikte_korting_str = "Onbekende korting"
                    bevat_fout = True

                controleer_euro += product.prijs_euro
                controleer_euro -= product.korting_euro

                # maak een knop om deze bestelling te verwijderen uit het mandje
                product.url_verwijder = reverse('Bestel:mandje-verwijder-product',
                                                kwargs={'product_pk': product.pk})

                mandje_is_leeg = False
            # for

            # nooit een negatief totaalbedrag tonen want we geven geen geld weg
            if controleer_euro < 0:
                controleer_euro = Decimal(0)

            controleer_euro += mandje.verzendkosten_euro
            controleer_euro += mandje.btw_euro_cat1
            controleer_euro += mandje.btw_euro_cat2
            controleer_euro += mandje.btw_euro_cat3

            if controleer_euro != mandje.totaal_euro:
                bevat_fout = True

        return mandje, producten, ontvanger2product_pks, mandje_is_leeg, bevat_fout

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        # omdat het heel raar is als het tellertje op het mandje niet overeenkomt
        # met de inhoud van het mandje, forceren we de telling hier nog een keer
        mandje_tel_inhoud(self.request)
        # eval_mandje_inhoud(self.request)

        # force dat het mandje icoon getoond wordt
        context['menu_toon_mandje'] = True

        mandje, producten, ontvanger2product_pks, mandje_is_leeg, bevat_fout = self._beschrijf_inhoud_mandje(account)

        if mandje:
            if mandje.transport == BESTEL_TRANSPORT_OPHALEN:
                context['toon_transport'] = True
                context['ophalen_ver'] = NhbVereniging.objects.get(ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR)

            elif mandje.transport == BESTEL_TRANSPORT_VERZEND:
                context['toon_transport'] = settings.WEBWINKEL_TRANSPORT_OPHALEN_MAG
                sporter = account.sporter_set.first()
                context['koper_sporter'] = sporter

        context['mandje_is_leeg'] = mandje_is_leeg
        context['mandje'] = mandje
        context['producten'] = producten
        context['bevat_fout'] = bevat_fout
        context['aantal_betalingen'] = len(ontvanger2product_pks.keys())
        context['url_kies_transport'] = reverse('Bestel:kies-transport')
        context['url_voorwaarden_wedstrijden'] = settings.VERKOOPVOORWAARDEN_WEDSTRIJDEN_URL
        context['url_voorwaarden_webwinkel'] = settings.VERKOOPVOORWAARDEN_WEBWINKEL_URL

        if not (bevat_fout or mandje_is_leeg):
            context['url_bestellen'] = reverse('Bestel:toon-inhoud-mandje')

        context['kruimels'] = (
            (None, 'Mandje'),
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de koper op de knop BESTELLING AFRONDEN gedrukt heeft
            Hier converteren we het mandje in een bevroren bestelling die afgerekend kan worden.
        """

        snel = str(request.POST.get('snel', ''))[:1]

        account = self.request.user

        bestel_mutatieverzoek_maak_bestellingen(account, snel == '1')
        # achtergrondtaak zet het mandje om in bestellingen

        # zorg dat de knop het juiste aantal toont
        mandje_tel_inhoud(request)

        # ga naar de pagina met alle bestellingen, zodat de betaling gestart kan worden
        url = reverse('Bestel:toon-bestellingen')
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
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):

        snel = str(request.POST.get('snel', ''))[:1]

        try:
            product_pk = str(kwargs['product_pk'])[:6]        # afkappen voor de veiligheid
            product_pk = int(product_pk)
        except (KeyError, ValueError, TypeError):
            raise Http404('Verkeerde parameter')

        # zoek de regel op in het mandje van de ingelogde gebruiker
        account = request.user
        try:
            mandje = BestelMandje.objects.prefetch_related('producten').get(account=account)
        except BestelMandje.DoesNotExist:
            raise Http404('Niet gevonden')
        else:
            qset = mandje.producten.filter(pk=product_pk)
            if qset.exists():
                # product zit in het mandje
                product = qset[0]

                bestel_mutatieverzoek_verwijder_product_uit_mandje(account, product, snel == '1')
                # achtergrondtaak geeft dit door aan de kalender/opleiding

                mandje_tel_inhoud(self.request)
            else:
                raise Http404('Niet gevonden in jouw mandje')

        url = reverse('Bestel:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


# end of file
