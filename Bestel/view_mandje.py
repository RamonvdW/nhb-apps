# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.models import ORGANISATIE_IFAA
from Bestel.mandje import mandje_tel_inhoud, eval_mandje_inhoud
from Bestel.models import BestelMandje
from Bestel.mutaties import (bestel_mutatieverzoek_maak_bestellingen,
                             bestel_mutatieverzoek_verwijder_product_uit_mandje)
from Betaal.models import BetaalInstellingenVereniging
from Functie.rol import Rollen, rol_get_huidige
from Wedstrijden.models import WEDSTRIJD_KORTING_COMBI, WEDSTRIJD_KORTING_SPORTER, WEDSTRIJD_KORTING_VERENIGING
from Plein.menu import menu_dynamics
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
            instellingen_nhb = ver_nr2instellingen[settings.BETAAL_VIA_NHB_VER_NR]
        except KeyError:
            # nog niet aangemaakt
            instellingen_nhb = None

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
                                         'wedstrijd_inschrijving__sporterboog__sporter')
                         .order_by('wedstrijd_inschrijving__pk'))

            for product in producten:
                # maak een beschrijving van deze regel
                product.beschrijving = beschrijving = list()
                product.kan_afrekenen = True

                if product.wedstrijd_inschrijving:
                    inschrijving = product.wedstrijd_inschrijving

                    tup = ('Reserveringsnummer', settings.TICKET_NUMMER_START__WEDSTRIJD + inschrijving.pk)
                    beschrijving.append(tup)

                    tup = ('Wedstrijd', inschrijving.wedstrijd.titel)
                    beschrijving.append(tup)

                    tup = ('Bij vereniging', inschrijving.wedstrijd.organiserende_vereniging.ver_nr_en_naam())
                    beschrijving.append(tup)

                    sessie = inschrijving.sessie
                    tup = ('Sessie', '%s om %s' % (sessie.datum, sessie.tijd_begin.strftime('%H:%M')))
                    beschrijving.append(tup)

                    sporterboog = inschrijving.sporterboog
                    tup = ('Sporter', '%s' % sporterboog.sporter.lid_nr_en_volledige_naam())
                    beschrijving.append(tup)

                    sporter_ver = sporterboog.sporter.bij_vereniging
                    if sporter_ver:
                        ver_naam = sporter_ver.ver_nr_en_naam()
                    else:
                        ver_naam = 'Onbekend'
                    tup = ('Lid bij', ver_naam)
                    beschrijving.append(tup)

                    tup = ('Boog', '%s' % sporterboog.boogtype.beschrijving)
                    beschrijving.append(tup)

                    if inschrijving.wedstrijd.organisatie == ORGANISATIE_IFAA:
                        tup = ('Klasse', '%s [%s]' % (inschrijving.wedstrijdklasse.beschrijving,
                                                      inschrijving.wedstrijdklasse.afkorting))
                    else:
                        tup = ('Klasse', '%s' % inschrijving.wedstrijdklasse.beschrijving)
                    beschrijving.append(tup)

                    if inschrijving.korting:
                        korting = inschrijving.korting
                        if korting.soort == WEDSTRIJD_KORTING_SPORTER:
                            product.gebruikte_korting_str = "Persoonlijke korting"
                        elif korting.soort == WEDSTRIJD_KORTING_VERENIGING:
                            product.gebruikte_korting_str = "Verenigingskorting"
                        elif korting.soort == WEDSTRIJD_KORTING_COMBI:
                            product.gebruikte_korting_str = "Combinatiekorting"
                            product.is_combi_korting = True
                            product.combi_reden = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.all()]
                        product.gebruikte_korting_str += ": %d%%" % korting.percentage
                    elif product.korting_euro:
                        # print('Onverwacht: product %s (pk=%s) heeft korting %s' % (product, product.pk, product.korting_euro))
                        product.gebruikte_korting_str = "Onbekende korting"
                        bevat_fout = True

                    controleer_euro += product.prijs_euro
                    controleer_euro -= product.korting_euro

                    ver_nr = product.wedstrijd_inschrijving.wedstrijd.organiserende_vereniging.ver_nr
                    try:
                        instellingen = ver_nr2instellingen[ver_nr]
                    except KeyError:
                        # geen instellingen, dus kan geen betaling ontvangen
                        product.kan_afrekenen = False
                    else:
                        if instellingen.akkoord_via_nhb:
                            ver_nr = settings.BETAAL_VIA_NHB_VER_NR
                            if instellingen_nhb is None or instellingen_nhb.mollie_api_key == '':
                                product.kan_afrekenen = False

                    try:
                        ontvanger2product_pks[ver_nr].append(product.pk)
                    except KeyError:
                        ontvanger2product_pks[ver_nr] = [product.pk]

                elif product.webwinkel_keuze:
                    webwinkel_keuze = product.webwinkel_keuze

                    tup = ('Webwinkel', '%s' % webwinkel_keuze.korte_beschrijving())
                    beschrijving.append(tup)

                    controleer_euro += product.prijs_euro

                else:
                    tup = ('Fout', 'Onbekend product')
                    beschrijving.append(tup)
                    bevat_fout = True
                    product.kan_afrekenen = False

                # maak een knop om deze bestelling te verwijderen uit het mandje
                product.url_verwijder = reverse('Bestel:mandje-verwijder-product',
                                                kwargs={'product_pk': product.pk})

                mandje_is_leeg = False
            # for

            # nooit een negatief totaalbedrag tonen want we geven geen geld weg
            if controleer_euro < 0.0:
                controleer_euro = 0.0

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

        context['mandje_is_leeg'] = mandje_is_leeg
        context['mandje'] = mandje
        context['producten'] = producten
        context['bevat_fout'] = bevat_fout
        context['aantal_betalingen'] = len(ontvanger2product_pks.keys())
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
