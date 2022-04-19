# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.operations import account_controleer_snelheid_verzoeken
from Betaal.models import BetaalInstellingenVereniging
from Bestel.operations import bestel_get_volgende_bestel_nr
from Functie.rol import Rollen, rol_get_huidige
from Kalender.mutaties import kalender_kortingscode_toepassen, kalender_verwijder_reservering
from Bestel.models import BestelMandje, Bestelling, BESTEL_KORTINGSCODE_MINLENGTH
from Bestel.mandje import mandje_tel_inhoud, eval_mandje_inhoud
from Overig.background_sync import BackgroundSync
from Plein.menu import menu_dynamics
from decimal import Decimal


TEMPLATE_MANDJE_TOON_INHOUD = 'bestel/toon-mandje.dtl'

kalender_mutaties_ping = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)


class ToonInhoudMandje(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een gebruiker de inhoud van zijn mandje zien """

    # class variables shared by all instances
    template_name = TEMPLATE_MANDJE_TOON_INHOUD
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    @staticmethod
    def _beschrijf_inhoud_mandje(account, maak_urls=True):
        """ gezamenlijke code voor het tonen van de inhoud van het mandje en het afrekenen """

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

        # zet de verenigingen om die akkoord hebben
        for ver_nr, instellingen in ver_nr2instellingen.items():
            if instellingen.akkoord_via_nhb:
                ver_nr2instellingen[ver_nr] = instellingen_nhb
        # for

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
                         .select_related('inschrijving',
                                         'inschrijving__wedstrijd',
                                         'inschrijving__sessie',
                                         'inschrijving__sporterboog',
                                         'inschrijving__sporterboog__boogtype',
                                         'inschrijving__sporterboog__sporter')
                         .order_by('inschrijving__pk'))

            for product in producten:
                # maak een beschrijving van deze regel
                product.beschrijving = beschrijving = list()
                product.kan_afrekenen = True

                if product.inschrijving:
                    inschrijving = product.inschrijving

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

                    if inschrijving.gebruikte_code:
                        korting = inschrijving.gebruikte_code
                        product.gebruikte_code_str = "code %s (korting: %d%%)" % (korting.code, korting.percentage)
                        if korting.combi_basis_wedstrijd:
                            product.is_combi_korting = True
                            product.combi_reden = [wedstrijd.titel for wedstrijd in korting.voor_wedstrijden.all()]
                    elif product.korting_euro:
                        product.gebruikte_code_str = "Onbekende code"
                        bevat_fout = True

                    controleer_euro += product.prijs_euro
                    controleer_euro -= product.korting_euro

                    if product.inschrijving:
                        ver_nr = product.inschrijving.wedstrijd.organiserende_vereniging.ver_nr
                        try:
                            instellingen = ver_nr2instellingen[ver_nr]
                        except KeyError:
                            # geen instellingen, dus kan geen betaling ontvangen
                            product.kan_afrekenen = False
                        else:
                            # check of de betalingen via de NHB mogen lopen
                            if instellingen is None:
                                # is None als er geen NHB instellingen zijn
                                product.kan_afrekenen = False
                            else:
                                if instellingen.akkoord_via_nhb:
                                    ver_nr = settings.BETAAL_VIA_NHB_VER_NR

                        try:
                            ontvanger2product_pks[ver_nr].append(product.pk)
                        except KeyError:
                            ontvanger2product_pks[ver_nr] = [product.pk]
                else:
                    tup = ('Fout', 'Onbekend product')
                    beschrijving.append(tup)
                    bevat_fout = True
                    product.kan_afrekenen = False

                if maak_urls:
                    # maak een knop om deze bestelling te verwijderen uit het mandje
                    product.url_verwijder = reverse('Bestel:mandje-verwijder-product',
                                                    kwargs={'product_pk': product.pk})

                mandje_is_leeg = False
            # for

            # nooit een negatief totaalbedrag tonen want we geven geen geld weg
            if controleer_euro < 0.0:
                controleer_euro = 0.0

            if controleer_euro != mandje.totaal_euro:
                bevat_fout = True

        return mandje, producten, ontvanger2product_pks, mandje_is_leeg, bevat_fout

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account = self.request.user

        eval_mandje_inhoud(self.request)

        mandje, producten, ontvanger2product_pks, mandje_is_leeg, bevat_fout = self._beschrijf_inhoud_mandje(account)

        context['mandje_is_leeg'] = mandje_is_leeg
        context['mandje'] = mandje
        context['producten'] = producten
        context['bevat_fout'] = bevat_fout
        context['aantal_betalingen'] = len(ontvanger2product_pks.keys())

        context['url_code_toevoegen'] = reverse('Bestel:mandje-code-toevoegen')
        if not (bevat_fout or mandje_is_leeg):
            if mandje and mandje.totaal_euro > 0:           # TODO: ondersteuning voor prijs=0
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
        account = self.request.user
        mandje, producten, ontvanger2product_pks, mandje_is_leeg, bevat_fout = self._beschrijf_inhoud_mandje(account, maak_urls=False)
        if bevat_fout or mandje_is_leeg or mandje is None:
            raise Http404('Afrekenen is niet mogelijk')

        for ver_nr, product_pks in ontvanger2product_pks.items():

            try:
                instellingen = BetaalInstellingenVereniging.objects.get(vereniging__ver_nr=ver_nr)
            except BetaalInstellingenVereniging.DoesNotExist:
                # vereniging kan niet betaald krijgen!
                # skip deze producten
                # TODO: hier zouden we een taak aan moeten maken en een paniek-mail sturen
                pass
            else:
                # neem een bestelnummer uit
                bestel_nr = bestel_get_volgende_bestel_nr()

                totaal_euro = Decimal(0)
                for product in producten:
                    if product.pk in product_pks:
                        totaal_euro += product.prijs_euro
                        totaal_euro -= product.korting_euro
                # for

                bestelling = Bestelling(
                                    bestel_nr=bestel_nr,
                                    account=account,
                                    ontvanger=instellingen,
                                    totaal_euro=totaal_euro)
                bestelling.save()

                bestelling.producten.set(product_pks)

                msg = "[%s] Bestelling aangemaakt met %s producten voor totaal euro=%s" % (
                                                bestelling.aangemaakt, len(product_pks), totaal_euro)
                bestelling.log = msg
                bestelling.save(update_fields=['log'])

                # haal deze producten uit het mandje
                to_be_removed = mandje.producten.filter(pk__in=product_pks)
                mandje.producten.remove(*to_be_removed)
        # for

        url = reverse('Bestel:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


class CodeToevoegenView(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        """ Voeg de code toe aan het mandje """

        snel = str(request.POST.get('snel', ''))[:1]

        code = ''
        for char in request.POST.get('code', '')[:40]:        # afkappen voor de veiligheid:
            if char.isalnum():
                code += char
        # for

        if len(code) >= BESTEL_KORTINGSCODE_MINLENGTH:
            account = request.user

            if account_controleer_snelheid_verzoeken(account):
                kalender_kortingscode_toepassen(account, code, snel == '1')

                mandje_tel_inhoud(self.request)

        # terug naar het mandje
        url = reverse('Bestel:toon-inhoud-mandje')

        return HttpResponseRedirect(url)


class VerwijderProductUitMandje(UserPassesTestMixin, View):

    # class variables shared by all instances
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft

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
            mandje, is_created = BestelMandje.objects.prefetch_related('producten').get_or_create(account=account)
        except BestelMandje.DoesNotExist:
            raise Http404('Niet gevonden')
        else:
            qset = mandje.producten.filter(pk=product_pk)
            if qset.exists():
                # product zit in het mandje
                product = qset[0]

                # verwijderen uit het mandje
                mandje.producten.remove(product)

                # maak de inschrijving ongedaan
                kalender_verwijder_reservering(product.inschrijving, snel == '1')

                mandje_tel_inhoud(self.request)
            else:
                raise Http404('Niet gevonden in jouw mandje')

        url = reverse('Bestel:toon-inhoud-mandje')
        return HttpResponseRedirect(url)


# end of file
