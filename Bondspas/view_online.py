# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.shortcuts import render, reverse
from django.views.generic import View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bondspas.operations import bepaal_jaar_bondspas, maak_bondspas_regels, maak_bondspas_jpeg_en_pdf
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Sporter.models import Sporter, get_sporter
import datetime
import base64


TEMPLATE_BONDSPAS_TONEN = 'bondspas/toon-bondspas-sporter.dtl'
TEMPLATE_BONDSPAS_VAN_TONEN = 'bondspas/toon-bondspas-van.dtl'

CONTENT_TYPE_PDF = 'application/pdf'


def _get_sporter_or_404(request):
    account = get_account(request)
    sporter = get_sporter(account)

    if not sporter:
        raise Http404('Geen bondspas voor dit account')

    if sporter.is_gast:
        raise Http404('Geen bondspas voor gast-accounts')

    if not sporter.is_actief_lid:
        raise Http404('Geen bondspas voor inactieve leden')

    return sporter


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

        _get_sporter_or_404(request)

        now = timezone.now()
        if now.month == 1:
            pas_jaar = bepaal_jaar_bondspas()
            if pas_jaar < now.year:
                context['is_oude_pas'] = True

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

        sporter = _get_sporter_or_404(request)

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
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
        sporter = _get_sporter_or_404(request)

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
        _, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        fname = 'bondspas_%s_%s.pdf' % (sporter.lid_nr, jaar_pas)

        response = HttpResponse(pdf_data, content_type=CONTENT_TYPE_PDF)
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname

        return response


class ToonBondspasBeheerderView(UserPassesTestMixin, View):

    template_name = TEMPLATE_BONDSPAS_VAN_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_BB, Rol.ROL_MLA, Rol.ROL_SUP)

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

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
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
        """ deze functie wordt aangeroepen als de download knop gebruikt wordt
            om een 'bondspas van ...' op te halen.
        """
        try:
            lid_nr = kwargs['lid_nr'][:6]       # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
            sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Geen valide parameter')

        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
        _, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        fname = 'bondspas_%s_%s.pdf' % (sporter.lid_nr, jaar_pas)

        response = HttpResponse(pdf_data, content_type=CONTENT_TYPE_PDF)
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname

        return response


class ToonBondspasVerenigingView(UserPassesTestMixin, View):

    template_name = TEMPLATE_BONDSPAS_VAN_TONEN
    raise_exception = True  # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_SEC, Rol.ROL_LA)

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

        if not sporter.bij_vereniging or sporter.bij_vereniging != self.functie_nu.vereniging:
            raise Http404('Verkeerde vereniging')

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
        img_data, _ = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        # base64 is nodig voor img in html
        context['bondspas_base64'] = base64.b64encode(img_data).decode()
        context['url_download'] = reverse('Bondspas:vereniging-bondspas-van', kwargs={'lid_nr': sporter.lid_nr})

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Vereniging:ledenlijst'), 'Ledenlijst'),
            (None, 'Bondspas tonen'),
        )

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ deze functie wordt aangeroepen als de download knop gebruikt wordt
            om een 'bondspas van ...' op te halen.
        """
        try:
            lid_nr = kwargs['lid_nr'][:6]       # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
            sporter = Sporter.objects.get(lid_nr=lid_nr)
        except Sporter.DoesNotExist:
            raise Http404('Geen valide parameter')

        if sporter.is_gast:
            raise Http404('Geen bondspas voor gast-accounts')

        if not sporter.bij_vereniging or sporter.bij_vereniging != self.functie_nu.vereniging:
            raise Http404('Verkeerde vereniging')

        jaar_pas = bepaal_jaar_bondspas()
        regels = maak_bondspas_regels(sporter, jaar_pas)
        _, pdf_data = maak_bondspas_jpeg_en_pdf(jaar_pas, sporter.lid_nr, regels)

        fname = 'bondspas_%s_%s.pdf' % (sporter.lid_nr, jaar_pas)

        response = HttpResponse(pdf_data, content_type=CONTENT_TYPE_PDF)
        response['Content-Disposition'] = 'attachment; filename="%s"' % fname

        return response


# end of file
