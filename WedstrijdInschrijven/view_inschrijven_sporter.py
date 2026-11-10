# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Kalender.definities import MAAND2URL
from Sporter.models import SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.models import Wedstrijd
from WedstrijdInschrijven.operations import get_sessies
from datetime import timedelta

TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_SPORTER = 'wedstrijdinschrijven/inschrijven-sporter.dtl'


def inschrijving_open_of_404(wedstrijd):
    """ Controleer dat de wedstrijd nog open is voor inschrijving.
        Zo niet, genereer dan fout 404
    """

    if wedstrijd.extern_beheerd:
        raise Http404('Externe inschrijving')

    now_date = timezone.now().date()
    wedstrijd.inschrijven_voor = wedstrijd.datum_begin - timedelta(days=wedstrijd.inschrijven_tot)
    is_voor_sluitingsdatum = now_date < wedstrijd.inschrijven_voor

    if not is_voor_sluitingsdatum:
        raise Http404('Inschrijving is gesloten')


class WedstrijdInschrijvenSporter(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf inschrijven voor een wedstrijd """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_SPORTER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rol.ROL_NONE

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """

        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:7]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        inschrijving_open_of_404(wedstrijd)

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        account = get_account(self.request)
        try:
            lid_nr = int(account.username)
        except ValueError:
            raise Http404('Bondsnummer ontbreekt')

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        context['sportersboog'] = list(SporterBoog
                                       .objects
                                       .exclude(sporter__is_overleden=True)
                                       .filter(sporter__lid_nr=lid_nr,
                                               sporter__is_actief_lid=True,              # moet actief lid zijn
                                               voor_wedstrijd=True,
                                               boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                       .select_related('sporter',
                                                       'sporter__bij_vereniging',
                                                       'boogtype')
                                       .order_by('boogtype__volgorde'))

        geselecteerd = None
        for sporterboog in context['sportersboog']:
            sporterboog.is_geselecteerd = False

            sporterboog.block_ver = sporterboog.sporter.bij_vereniging.geen_wedstrijden

            sporterboog.url_selecteer = reverse('WedstrijdInschrijven:inschrijven-sporter-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})

            if boog_afk == sporterboog.boogtype.afkorting.lower():
                geselecteerd = sporterboog
        # for

        context['toon_kies_wedstrijdboog'] = len(context['sportersboog']) > 1

        if not geselecteerd and len(context['sportersboog']) > 0:
            geselecteerd = context['sportersboog'][0]

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wisselknop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            kan_aanmelden = False
            if not geselecteerd.block_ver:
                voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
                tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
                (context['sessies'],
                 context['leeftijd'],
                 context['leeftijdsklassen'],
                 geslacht,
                 context['toon_sessie_beschrijvingen']) = tups

                ingeschreven_op_sessie = None
                for sessie in context['sessies']:
                    if sessie.kan_aanmelden:
                        kan_aanmelden = True
                    if sessie.al_ingeschreven:
                        ingeschreven_op_sessie = sessie
                # for
                context['ingeschreven_op_sessie'] = ingeschreven_op_sessie

                # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
                # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
                if geslacht == '?':
                    context['uitleg_geslacht'] = True
                    if kan_aanmelden:
                        context['uitleg_geslacht'] = False
            else:
                context['leeftijd'] = '?'

            context['kan_aanmelden'] = kan_aanmelden

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('WedstrijdInschrijven:inschrijven-toevoegen-aan-mandje')

        url_terug = reverse('Kalender:simpel',
                            kwargs={'jaar_of_maand': 'maand',
                                    'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven sporter')
        )

        return context

# end of file
