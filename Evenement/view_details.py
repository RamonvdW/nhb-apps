# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import TemplateView
from Account.models import get_account
from Evenement.models import Evenement
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Kalender.view_maand import MAAND2URL
from datetime import timedelta


TEMPLATE_EVENEMENT_DETAILS = 'evenement/details.dtl'


class DetailsView(TemplateView):

    """ Via deze view krijgen sporters details van het evenement te zien """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_DETAILS

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            evenement_pk = str(kwargs['evenement_pk'])[:6]     # afkappen voor de veiligheid
            evenement = (Evenement
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .get(pk=evenement_pk))
        except Evenement.DoesNotExist:
            raise Http404('Evenement niet gevonden')

        context['evenement'] = evenement

        now_date = timezone.now().date()

        evenement.inschrijven_voor = evenement.datum - timedelta(days=evenement.inschrijven_tot)
        evenement.inschrijven_dagen = (evenement.inschrijven_voor - now_date).days
        evenement.inschrijven_let_op = (evenement.inschrijven_dagen <= 7)

        if evenement.inschrijven_dagen < -30:
            evenement.is_ter_info = True

        zoekterm = evenement.locatie.adres
        zoekterm = zoekterm.replace('\n', ' ').replace('\r', '').replace('  ', ' ')
        context['url_map'] = 'https://google.nl/maps?' + urlencode({'q': zoekterm})

        # inschrijven moet voor de sluitingsdatum
        context['is_voor_sluitingsdatum'] = now_date < evenement.inschrijven_voor

        # om aan te melden is een account nodig
        # en je moet lid zijn van de KHSN (dus: geen gast-account)
        evenement.begrenzing_str = "KHSN leden"

        account = get_account(self.request)
        context['kan_aanmelden'] = account.is_authenticated and not account.is_gast
        context['hint_inloggen'] = not account.is_authenticated

        rol_nu, functie_nu = rol_get_huidige_functie(self.request)
        is_organiserende_hwl = (rol_nu == Rol.ROL_HWL and functie_nu.vereniging == evenement.organiserende_vereniging)
        context['is_organiserende_hwl'] = is_organiserende_hwl
        if is_organiserende_hwl:
            context['kan_aanmelden'] = False

        if context['kan_aanmelden']:
            context['menu_toon_mandje'] = True

            if context['is_voor_sluitingsdatum']:
                context['url_inschrijven_sporter'] = reverse('Evenement:inschrijven-sporter',
                                                             kwargs={'evenement_pk': evenement.pk})
                context['url_inschrijven_groepje'] = reverse('Evenement:inschrijven-groepje',
                                                             kwargs={'evenement_pk': evenement.pk})
                context['url_inschrijven_familie'] = reverse('Evenement:inschrijven-familie',
                                                             kwargs={'evenement_pk': evenement.pk})

        # inschrijf sectie (kaartjes) tonen voor dit evenement?
        context['toon_inschrijven'] = context['is_voor_sluitingsdatum'] and not is_organiserende_hwl

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': evenement.datum.year,
                                    'maand': MAAND2URL[evenement.datum.month],
                                    'soort': 'alle',
                                    'bogen': 'auto',
                                    'discipline': 'alle'})
        context['kruimels'] = (
            (url_terug, 'Kalender'),
            (None, 'Details evenement'),
        )

        return context


# end of file
