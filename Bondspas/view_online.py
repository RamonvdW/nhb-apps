# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import render, reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bondspas.operations import bepaal_jaar_bondspas_en_wedstrijden, maak_bondspas_regels, maak_bondspas_jpeg_en_pdf
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Sporter.models import Sporter, get_sporter
import base64


TEMPLATE_BONDSPAS_TONEN = 'bondspas/toon-bondspas-sporter.dtl'
TEMPLATE_BONDSPAS_VAN_TONEN = 'bondspas/toon-bondspas-van.dtl'

CONTENT_TYPE_PDF = 'application/pdf'


class ToonBondspasView(UserPassesTestMixin, View):

    """ Deze view kan de bondspas tonen, of een scherm met 'even wachten, we zoeken je pas op' """

    template_name = TEMPLATE_BONDSPAS_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn. Rol is niet belangrijk.
        return rol_get_huidige(self.request) != Rol.ROL_NONE

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        # bondspas wordt opgehaald nadat de pagina getoond kan worden
        context['url_dynamic'] = reverse('Bondspas:dynamic-ophalen')
        context['url_download'] = reverse('Bondspas:dynamic-download')

        account = get_account(request)
        sporter = get_sporter(account)
        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        context['kruimels'] = (
            (reverse('Sporter:profiel'), 'Mijn pagina'),
            (None, 'Toon bondspas'),
        )

        # toon een pagina die wacht op de download
        return render(request, self.template_name, context)


class DynamicBondspasOphalenView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn. Rol is niet belangrijk.
        return rol_get_huidige(self.request) != Rol.ROL_NONE

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de webpagina via een stukje javascript de bondspas ophaalt
            nadat de hele HTML binnen is en de pagina getoond kan worden.

            Dit is een POST by-design, om caching te voorkomen.
        """

        account = get_account(request)
        sporter = get_sporter(account)
        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        jaar_pas, jaar_wedstrijden = bepaal_jaar_bondspas_en_wedstrijden()
        regels = maak_bondspas_regels(sporter, jaar_pas, jaar_wedstrijden)
        img_data, _ = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        # base64 is nodig voor img in html
        # alternatief is javascript laten tekenen op een canvas en base64 maken met dataToUrl
        out = dict()
        out['bondspas_base64'] = base64.b64encode(img_data).decode()

        return JsonResponse(out)


class DynamicBondspasDownloadView(UserPassesTestMixin, View):

    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        # gebruiker moet ingelogd zijn. Rol is niet belangrijk.
        return rol_get_huidige(self.request) != Rol.ROL_NONE

    @staticmethod
    def post(request, *args, **kwargs):
        """ Deze functie wordt aangeroepen als de gebruiker op de download knop druk.

            Dit is een POST by-design, om caching te voorkomen.
        """

        account = get_account(request)
        sporter = get_sporter(account)
        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        jaar_pas, jaar_wedstrijden = bepaal_jaar_bondspas_en_wedstrijden()
        regels = maak_bondspas_regels(sporter, jaar_pas, jaar_wedstrijden)
        _, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        fname = 'bondspas_%s_%s.pdf' % (sporter.lid_nr, jaar_pas)

        response = HttpResponse(pdf_data, content_type=CONTENT_TYPE_PDF)
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname

        return response


class ToonBondspasBeheerderView(UserPassesTestMixin, View):

    template_name = TEMPLATE_BONDSPAS_VAN_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu in (Rol.ROL_BB, Rol.ROL_MLA, Rol.ROL_SUP)

    def get(self, request, *args, **kwargs):
        """ called by the template system to get the context data for the template """
        context = dict()

        try:
            lid_nr = kwargs['lid_nr'][:6]       # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
            sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Geen valide parameter')

        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        jaar_pas, jaar_wedstrijden = bepaal_jaar_bondspas_en_wedstrijden()
        regels = maak_bondspas_regels(sporter, jaar_pas, jaar_wedstrijden)
        img_data, _ = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        # base64 is nodig voor img in html
        context['bondspas_base64'] = base64.b64encode(img_data).decode()
        context['url_download'] = reverse('Bondspas:toon-bondspas-van', kwargs={'lid_nr': sporter.lid_nr})

        context['kruimels'] = (
            (reverse('Overig:activiteit'), 'Account activiteit'),
            (None, 'Bondspas tonen'),
        )

        return render(request, self.template_name, context)

    @staticmethod
    def post(request, *args, **kwargs):
        try:
            lid_nr = kwargs['lid_nr'][:6]       # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
            sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Geen valide parameter')

        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        jaar_pas, jaar_wedstrijden = bepaal_jaar_bondspas_en_wedstrijden()
        regels = maak_bondspas_regels(sporter, jaar_pas, jaar_wedstrijden)
        _, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        fname = 'bondspas_%s_%s.pdf' % (sporter.lid_nr, jaar_pas)

        response = HttpResponse(pdf_data, content_type=CONTENT_TYPE_PDF)
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname

        return response


# end of file
