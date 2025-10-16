# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from django.conf import settings
from django.views.generic import TemplateView
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Site.core.static import static_safe
from Webwinkel.models import WebwinkelProduct


TEMPLATE_WEBWINKEL_OVERZICHT = 'webwinkel/overzicht.dtl'


class OverzichtView(TemplateView):

    """ Via deze view laten we alle producten zien als kaartjes """

    # class variables shared by all instances
    template_name = TEMPLATE_WEBWINKEL_OVERZICHT

    @staticmethod
    def _get_producten():
        producten = (WebwinkelProduct
                     .objects
                     .exclude(mag_tonen=False)
                     .select_related('omslag_foto')
                     .order_by('volgorde'))

        objs = list()

        prev_sectie = None
        prev_titel = ''
        for product in producten:
            # kleding in verschillende maten hebben dezelfde omslag titel
            # toon alleen de eerste
            if product.omslag_titel != prev_titel:
                objs.append(product)
                prev_titel = product.omslag_titel

            if product.sectie != prev_sectie:
                if prev_sectie is not None:
                    product.sectie_afsluiten = True
                product.nieuwe_sectie = True
                prev_sectie = product.sectie

            if product.omslag_foto:
                product.omslag_foto_src = static_safe("webwinkel_fotos/" + product.omslag_foto.locatie)
            else:
                product.omslag_foto_src = static_safe("design/logo_khsn_192x192.webp")

            if not product.onbeperkte_voorraad:
                if product.aantal_op_voorraad < 1:
                    # voorkom uitverkocht als het eerste product op is
                    if not product.kleding_maat:
                        product.is_uitverkocht = True

            product.is_extern = product.beschrijving.startswith('http')
            if product.is_extern:
                # is_extern geeft ook icoontje in de rechter bovenhoek
                product.url_details = product.beschrijving
            else:
                product.url_details = reverse('Webwinkel:product', kwargs={'product_pk': product.pk})
        # for

        return objs

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        context['producten'] = self._get_producten()

        # iedereen mag de informatie over de spelden zien
        # begrenzing voor bestellen (alleen leden) volgt verderop
        if settings.WEBWINKEL_TOON_PRESTATIESPELDEN:
            context['url_spelden'] = reverse('Spelden:begin')
            context['img_spelden'] = static_safe('spelden/ster_1200.webp')

        if rol_get_huidige(self.request) == Rol.ROL_SPORTER:
            context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (None, 'Webwinkel'),
        )

        return context


# end of file
