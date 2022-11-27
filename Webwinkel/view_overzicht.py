# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import localize
from django.shortcuts import render
from django.templatetags.static import static
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Bestel.operations.mandje import mandje_tel_inhoud
from Bestel.operations.mutaties import bestel_mutatieverzoek_webwinkel_keuze
from Plein.menu import menu_dynamics
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze


TEMPLATE_WEBWINKEL_OVERZICHT = 'webwinkel/overzicht.dtl'
TEMPLATE_WEBWINKEL_PRODUCT = 'webwinkel/product.dtl'
TEMPLATE_WEBWINKEL_TOEGEVOEGD_AAN_MANDJE = 'webwinkel/toegevoegd-aan-mandje.dtl'


class OverzichtView(UserPassesTestMixin, TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_OVERZICHT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['producten'] = producten = (WebwinkelProduct
                                            .objects
                                            .exclude(mag_tonen=False)
                                            .select_related('omslag_foto')
                                            .order_by('sectie',
                                                      'volgorde'))

        prev_sectie = None
        for product in producten:
            if product.sectie != prev_sectie:
                if prev_sectie is not None:
                    product.sectie_afsluiten = True
                product.nieuwe_sectie = True
                prev_sectie = product.sectie

            if product.omslag_foto:
                product.omslag_foto_src = static("webwinkel_fotos/" + product.omslag_foto.locatie)
            else:
                product.omslag_foto_src = static("plein/logo_nhb_32x32.png")

            if not product.onbeperkte_voorraad:
                if product.aantal_op_voorraad < 1:
                    product.is_uitverkocht = True

            product.url_details = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})
        # for

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (None, 'Webwinkel'),
        )

        menu_dynamics(self.request, context)
        return context


class ProductView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan 1 product ingezien en besteld worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_PRODUCT
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            product_pk = kwargs['product_pk'][:6]             # afkappen voor de veiligheid
            product_pk = int(product_pk)
            product = (WebwinkelProduct
                       .objects
                       .prefetch_related('fotos')
                       .get(pk=product_pk,
                            mag_tonen=True))
        except (ValueError, TypeError, WebwinkelProduct.DoesNotExist):
            raise Http404('Product niet gevonden')

        context['product'] = product

        if product.eenheid:
            aantal_enkel, aantal_meer = product.eenheid.split(',')
        else:
            aantal_enkel = aantal_meer = 'stuks'

        if not product.onbeperkte_voorraad:
            product.aantal_str = '%s %s' % (product.aantal_op_voorraad, aantal_meer)

        product.sel_opts = sel_opts = list()
        opties = product.bestel_begrenzing.strip()
        if not opties:
            opties = '1-5'

        # voorbeeld: 1-10,20,25,30,50
        spl = opties.split(',')
        for optie in spl:
            if '-' in optie:
                van, tot = optie.split('-')
            else:
                van = tot = int(optie)

            for aantal in range(int(van), int(tot) + 1):
                prijs = product.prijs_euro * aantal

                if aantal == 1:
                    msg = '1 %s (€ %s)' % (aantal_enkel, localize(prijs))
                else:
                    msg = '%s %s (€ %s)' % (aantal, aantal_meer, localize(prijs))
                sel_opts.append((aantal, msg))
            # for
        # for

        context['fotos'] = fotos = product.fotos.order_by('volgorde')
        for foto in fotos:
            foto.img_src = static("webwinkel_fotos/" + foto.locatie)
            foto.thumb_src = static("webwinkel_fotos/" + foto.locatie_thumb)
        # for

        context['url_toevoegen'] = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})

        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (None, 'Product')
        )

        menu_dynamics(self.request, context)
        return context

    def post(self, request, *args, **kwargs):

        try:
            product_pk = kwargs['product_pk'][:6]           # afkappen voor de veiligheid
            product_pk = int(product_pk)
            product = (WebwinkelProduct
                       .objects
                       .prefetch_related('fotos')
                       .get(pk=product_pk,
                            mag_tonen=True))
        except (ValueError, TypeError, WebwinkelProduct.DoesNotExist):
            raise Http404('Product niet gevonden')

        aantal = request.POST.get('aantal', '')[:6]         # afkappen voor de veiligheid
        try:
            aantal = int(aantal)
        except (ValueError, TypeError):
            raise Http404('Foutieve parameter')

        # check of het aantal toegestaan is
        is_goed = False

        opties = product.bestel_begrenzing.strip()
        if not opties:
            opties = '1-5'

        # voorbeeld: 1-10,20,25,30,50
        spl = opties.split(',')
        for optie in spl:
            if '-' in optie:
                van, tot = optie.split('-')
                if int(van) <= aantal <= int(tot):
                    is_goed = True
                    break
            else:
                if aantal == int(optie):
                    is_goed = True
                    break
        # for

        # voorkom toevoegen als er niet genoeg voorraad is
        if not product.onbeperkte_voorraad and aantal > product.aantal_op_voorraad:
            is_goed = False

        if not is_goed:
            raise Http404('Foutieve parameter (2)')

        account_koper = request.user
        now = timezone.now()
        totaal_euro = product.prijs_euro * aantal

        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] %s producten toegevoegd aan het mandje van %s\n" % (stamp_str,
                                                                        aantal,
                                                                        account_koper.get_account_full_name())

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=account_koper,
                        product=product,
                        aantal=aantal,
                        totaal_euro=totaal_euro,
                        log=msg)
        keuze.save()

        # zet dit verzoek door naar de achtergrondtaak
        snel = str(request.POST.get('snel', ''))[:1]
        bestel_mutatieverzoek_webwinkel_keuze(account_koper, keuze, snel == '1')

        mandje_tel_inhoud(self.request)

        # geeft de gebruiker een pagina om naar het mandje te gaan of verder te winkelen
        context = dict()

        url_overzicht = reverse('Webwinkel:overzicht')
        url_product = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})

        context['menu_toon_mandje'] = True
        context['url_verder'] = url_overzicht
        context['url_mandje'] = reverse('Bestel:toon-inhoud-mandje')

        context['kruimels'] = (
            (url_overzicht, 'Webwinkel'),
            (url_product, 'Product'),
            (None, 'Toegevoegd aan mandje')
        )

        menu_dynamics(self.request, context)

        return render(request, TEMPLATE_WEBWINKEL_TOEGEVOEGD_AAN_MANDJE, context)


# end of file
