# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Functie.definities import Rol
from Functie.rol import rol_get_huidige
from Kalender.definities import MAAND2URL
from Sporter.models import Sporter, SporterBoog, get_sporter
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving
from WedstrijdInschrijven.helpers import inschrijving_open_of_404
from WedstrijdInschrijven.operations import get_sessies

TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_FAMILIE = 'wedstrijdinschrijven/inschrijven-familie.dtl'


class WedstrijdInschrijvenFamilie(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf en familie inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_FAMILIE
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

        # begrens de mogelijkheden tot leden met dezelfde adres_code als de ingelogde gebruiker
        account = get_account(self.request)
        sporter = get_sporter(account)
        if not sporter:     # pragma: no cover
            raise Http404('Account is niet compleet')

        adres_code = sporter.adres_code

        # fall-back als dit de geselecteerde sporter is
        context['sporter'] = sporter

        try:
            lid_nr = str(kwargs['lid_nr'])[:6]                  # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # val terug op de ingelogde gebruiker
            lid_nr = sporter.lid_nr
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                # val terug op de ingelogde gebruiker
                lid_nr = sporter.lid_nr

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        context['familie'] = list(SporterBoog
                                  .objects
                                  .exclude(sporter__is_overleden=True)
                                  .filter(sporter__adres_code=adres_code,
                                          sporter__is_actief_lid=True,
                                          voor_wedstrijd=True,
                                          boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                  .select_related('sporter',
                                                  'sporter__bij_vereniging',
                                                  'boogtype')
                                  .order_by('sporter__sinds_datum',
                                            'sporter__lid_nr',
                                            'boogtype__volgorde')[:50])

        sporter_pks = list()
        geselecteerd = None
        for sporterboog in context['familie']:
            sporterboog.is_geselecteerd = False

            sporterboog.block_ver = sporterboog.sporter.bij_vereniging.geen_wedstrijden

            sporterboog.url_selecteer = reverse('WedstrijdInschrijven:inschrijven-familie-lid-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'lid_nr': sporterboog.sporter.lid_nr,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})

            if sporterboog.sporter.pk not in sporter_pks:
                sporter_pks.append(sporterboog.sporter.pk)

            if sporterboog.sporter.lid_nr == lid_nr:
                if boog_afk == sporterboog.boogtype.afkorting.lower():
                    geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['familie']) > 0:
            geselecteerd = context['familie'][0]

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            if not geselecteerd.block_ver:
                voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
                tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
                (context['sessies'],
                 _,
                 context['leeftijdsklassen'],
                 geslacht,
                 context['toon_sessie_beschrijvingen']) = tups

                # kijk of deze sporter al ingeschreven is, want maximaal aanmelden met 1 boog
                sessie_pk2inschrijving = dict()
                for inschrijving in (WedstrijdInschrijving
                                     .objects
                                     .filter(wedstrijd=wedstrijd,
                                             sporterboog__sporter=geselecteerd.sporter)
                                     .select_related('sessie',
                                                     'sporterboog',
                                                     'sporterboog__sporter')):
                    sessie_pk2inschrijving[inschrijving.sessie.pk] = inschrijving
                # for

                kan_aanmelden = False
                al_ingeschreven = False
                for sessie in context['sessies']:
                    try:
                        inschrijving = sessie_pk2inschrijving[sessie.pk]
                    except KeyError:
                        # sporter is nog niet ingeschreven
                        if sessie.kan_aanmelden:
                            kan_aanmelden = True
                    else:
                        # sporter is ingeschreven
                        al_ingeschreven = True
                        context['inschrijving'] = inschrijving
                        inschrijving.status_str = WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR[inschrijving.status]
                # for

                context['al_ingeschreven'] = al_ingeschreven

                # toon ook de sessie als de sporter geen compatibele boog heeft
                context['kan_aanmelden'] = kan_aanmelden

                # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
                # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
                if geslacht == '?':
                    context['uitleg_geslacht'] = True
                    if kan_aanmelden:
                        context['uitleg_geslacht'] = False
            else:
                context['kan_aanmelden'] = False

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)
        else:
            # sporter heeft geen boog voorkeur, dus mag waarschijnlijk niet schieten
            # context['sporter'] is al ingevuld (nodig in de template)
            pass

        # voeg niet-schietende sporters toe aan de lijst
        for sporter in (Sporter
                        .objects
                        .filter(adres_code=adres_code)
                        .order_by('sinds_datum',
                                  'lid_nr'))[:10]:
            if sporter.pk not in sporter_pks:
                dummy = SporterBoog(sporter=sporter)
                dummy.geen_boog = True
                dummy.is_geselecteerd = False
                context['familie'].append(dummy)
        # for

        context['menu_toon_mandje'] = True

        context['url_toevoegen'] = reverse('WedstrijdInschrijven:inschrijven-toevoegen-aan-mandje')

        url_terug = reverse('Kalender:simpel',
                            kwargs={'jaar_of_maand': 'maand',
                                    'jaar': wedstrijd.datum_begin.year,
                                    'maand': MAAND2URL[wedstrijd.datum_begin.month]})

        context['kruimels'] = (
            (url_terug, 'Wedstrijdkalender'),
            (reverse('Wedstrijden:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Wedstrijd details'),
            (None, 'Inschrijven familie'),
        )

        return context


# end of file
