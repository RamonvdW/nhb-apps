# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.shortcuts import render
from django.views.generic import TemplateView
from Account.models import get_account
from Bestelling.operations import mandje_tel_inhoud, bestel_mutatieverzoek_webwinkel_keuze
from Betaal.format import format_bedrag_euro
from Site.core.static import static_safe
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze


TEMPLATE_WEBWINKEL_PRODUCT = 'webwinkel/product.dtl'
TEMPLATE_WEBWINKEL_TOEGEVOEGD_AAN_MANDJE = 'webwinkel/toegevoegd-aan-mandje.dtl'


class ProductView(TemplateView):

    """ Via deze view kan 1 product ingezien en besteld worden """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_PRODUCT

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

        if product.kleding_maat:
            product.sel_opts_maat = sel_opts = list()
            voorraad = 0
            for maat in (WebwinkelProduct
                         .objects
                         .filter(omslag_titel=product.omslag_titel)
                         .order_by('volgorde')):

                msg = product.omslag_titel + ', maat %s' % maat.kleding_maat

                if maat.aantal_op_voorraad > 0:
                    voorraad += maat.aantal_op_voorraad
                    msg += ' (nog %s beschikbaar)' % maat.aantal_op_voorraad
                else:
                    msg += '  (uitverkocht)'

                tup = (maat.kleding_maat, msg)
                sel_opts.append(tup)
            # for

            product.aantal_op_voorraad = voorraad

        if product.eenheid:
            if ',' in product.eenheid:
                aantal_enkel, aantal_meer = product.eenheid.split(',')
            else:
                aantal_enkel = aantal_meer = product.eenheid
        else:
            aantal_enkel = aantal_meer = 'stuks'

        if product.onbeperkte_voorraad:
            limiet_aantal = 99999
        else:
            product.aantal_str = '%s %s' % (product.aantal_op_voorraad, aantal_meer)
            limiet_aantal = product.aantal_op_voorraad

        product.sel_opts_aantal = sel_opts = list()
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
                if aantal <= limiet_aantal:
                    prijs = product.prijs_euro * aantal

                    if aantal == 1:
                        msg = '1 %s (%s)' % (aantal_enkel, format_bedrag_euro(prijs))
                    else:
                        msg = '%s %s (%s)' % (aantal, aantal_meer, format_bedrag_euro(prijs))
                    sel_opts.append((aantal, msg))
            # for
        # for

        if len(sel_opts) == 0:
            sel_opts.append((0, 'Sorry, niet beschikbaar'))

        context['fotos'] = fotos = product.fotos.order_by('volgorde')
        is_eerste = True
        nr = 0
        for foto in fotos:
            nr += 1
            foto.id_img = "id_img_%s" % nr
            foto.id_thumb = "id_thumb_%s" % nr
            foto.img_src = static_safe("webwinkel_fotos/" + foto.locatie)
            foto.thumb_src = static_safe("webwinkel_fotos/" + foto.locatie_thumb)
            foto.is_eerste = is_eerste
            is_eerste = False
            context['heeft_fotos'] = True
        # for

        context['js_fotos'] = [(foto.volgorde, foto.id_thumb, foto.id_img)
                               for foto in fotos]

        if not self.request.user.is_authenticated:
            context['moet_inloggen'] = True
        else:
            context['url_toevoegen'] = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (reverse('Webwinkel:overzicht'), 'Webwinkel'),
            (None, 'Product')
        )

        return context

    def post(self, request, *args, **kwargs):

        account_koper = get_account(self.request)
        if not account_koper.is_authenticated:
            raise Http404('Geen toegang')

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

        if product.kleding_maat:
            maat = request.POST.get('maat', '')[:10]        # afkappen voor de veiligheid

            # zoek het juiste product erbij
            try:
                product = (WebwinkelProduct
                           .objects
                           .prefetch_related('fotos')
                           .get(omslag_titel=product.omslag_titel,
                                mag_tonen=True,
                                kleding_maat=maat))
            except (ValueError, TypeError, WebwinkelProduct.DoesNotExist, WebwinkelProduct.MultipleObjectsReturned):
                raise Http404('Product met maat niet gevonden')

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

        now = timezone.now()
        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] %s producten toegevoegd aan het mandje van %s\n" % (stamp_str,
                                                                        aantal,
                                                                        account_koper.get_account_full_name())

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        product=product,
                        aantal=aantal,
                        log=msg)
        keuze.save()

        # zet dit verzoek door naar de achtergrondtaak
        snel = str(request.POST.get('snel', ''))[:1]
        bestel_mutatieverzoek_webwinkel_keuze(account_koper, keuze, snel == '1')

        mandje_tel_inhoud(self.request, account_koper)

        # geeft de gebruiker een pagina om naar het mandje te gaan of verder te winkelen
        context = dict()

        url_overzicht = reverse('Webwinkel:overzicht')
        url_product = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})

        context['menu_toon_mandje'] = True
        context['url_verder'] = url_overzicht
        context['url_mandje'] = reverse('Bestelling:toon-inhoud-mandje')

        context['kruimels'] = (
            (url_overzicht, 'Webwinkel'),
            (url_product, 'Product'),
            (None, 'Toegevoegd aan mandje')
        )

        return render(request, TEMPLATE_WEBWINKEL_TOEGEVOEGD_AAN_MANDJE, context)


# end of file
