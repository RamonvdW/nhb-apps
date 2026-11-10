# -*- coding: utf-8 -*-

#  Copyright (c) 2021-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestelling.operations import bestel_mutatieverzoek_handmatig_toevoegen_wedstrijd
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Sporter.models import SporterBoog
from Sporter.operations import get_sporter_voorkeuren
from Wedstrijden.definities import WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD, WEDSTRIJD_INSCHRIJVING_STATUS_TO_STR
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving
from WedstrijdInschrijven.operations import get_sessies

TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_HANDMATIG = 'wedstrijdinschrijven/inschrijven-handmatig.dtl'


class WedstrijdInschrijvenHandmatig(UserPassesTestMixin, TemplateView):

    """ Via deze view kan de HWL een sporter inschrijven """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_INSCHRIJVEN_HANDMATIG
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_HWL

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

        if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
            raise PermissionDenied('Wedstrijd van andere vereniging')

        wedstrijd_boogtype_pks = list(wedstrijd.boogtypen.all().values_list('pk', flat=True))

        try:
            lid_nr = str(kwargs['lid_nr'])[:6]                  # afkappen voor de veiligheid
            lid_nr = int(lid_nr)
        except (KeyError, TypeError, ValueError):
            # val terug op de ingelogde gebruiker
            lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= lid_nr <= 999999):
                # val terug op de ingelogde gebruiker
                lid_nr = -1

        try:
            boog_afk = str(kwargs['boog_afk'])[:3]              # afkappen voor de veiligheid
            boog_afk = boog_afk.lower()
        except KeyError:
            # val terug op "geen keuze"
            boog_afk = ''

        try:
            zoek_lid_nr = self.request.GET['bondsnummer']
            zoek_lid_nr = str(zoek_lid_nr)[:6]                  # afkappen voor de veiligheid
            zoek_lid_nr = int(zoek_lid_nr)
        except (KeyError, TypeError, ValueError):
            # geen zoekparameter of slechte zoekterm
            zoek_lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= zoek_lid_nr <= 999999):
                zoek_lid_nr = -1

        if zoek_lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .exclude(sporter__is_overleden=True)
                                           .exclude(sporter__bij_vereniging=None)
                                           .filter(sporter__lid_nr=zoek_lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        elif lid_nr != -1:
            context['sportersboog'] = list(SporterBoog
                                           .objects
                                           .exclude(sporter__is_overleden=True)
                                           .exclude(sporter__bij_vereniging=None)
                                           .filter(sporter__lid_nr=lid_nr,
                                                   voor_wedstrijd=True,
                                                   boogtype__pk__in=wedstrijd_boogtype_pks)  # alleen toegestane bogen
                                           .select_related('sporter',
                                                           'sporter__bij_vereniging',
                                                           'boogtype')
                                           .order_by('boogtype__volgorde'))
        else:
            # toon alleen het zoekveld
            context['sportersboog'] = list()

        geselecteerd = None
        for sporterboog in context['sportersboog']:
            sporterboog.is_geselecteerd = False

            sporterboog.url_selecteer = reverse('WedstrijdInschrijven:inschrijven-handmatig-lid-boog',
                                                kwargs={'wedstrijd_pk': wedstrijd.pk,
                                                        'lid_nr': sporterboog.sporter.lid_nr,
                                                        'boog_afk': sporterboog.boogtype.afkorting.lower()})
            if boog_afk == sporterboog.boogtype.afkorting.lower():
                geselecteerd = sporterboog
        # for

        if not geselecteerd and len(context['sportersboog']) > 0:
            geselecteerd = context['sportersboog'][0]

        if len(context['sportersboog']) > 1:
            context['toon_sportersboog'] = True

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wisselknop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            voorkeuren = get_sporter_voorkeuren(geselecteerd.sporter)
            tups = get_sessies(wedstrijd, geselecteerd.sporter, voorkeuren, geselecteerd.boogtype.pk)
            (context['sessies'],
             context['leeftijd'],
             context['leeftijdsklassen'],
             geslacht,
             context['toon_sessie_beschrijvingen']) = tups

            # kijk of deze sporter al ingeschreven is
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
            context['kan_aanmelden'] = kan_aanmelden
            context['al_ingeschreven'] = al_ingeschreven

            # als de sporter geslacht 'anders' heeft en nog geen keuze gemaakt heeft voor wedstrijden
            # kijk dan of er een gender-neutrale sessie is waar op ingeschreven kan worden
            if geslacht == '?':
                context['uitleg_geslacht'] = True
                if kan_aanmelden:
                    context['uitleg_geslacht'] = False

            context['prijs_euro_sporter'] = wedstrijd.bepaal_prijs_voor_sporter(geselecteerd.sporter)

        context['url_zoek'] = reverse('WedstrijdInschrijven:inschrijven-handmatig',
                                      kwargs={'wedstrijd_pk': wedstrijd.pk})

        context['url_toevoegen'] = context['url_zoek']

        context['kruimels'] = (
            (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
            (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
            (reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wedstrijd.pk}), 'Aanmeldingen'),
            (None, 'Handmatig toevoegen'),
        )

        return context

    def post(self, request, *args, **kwargs):

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:7]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging',
                                         'locatie')
                         .prefetch_related('boogtypen',
                                           'sessies',
                                           'wedstrijdklassen')
                         .get(pk=wedstrijd_pk))
        except (ValueError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
            raise PermissionDenied('Wedstrijd van andere vereniging')

        sporterboog_str = request.POST.get('sporterboog', '')[:7]   # afkappen voor de veiligheid
        sessie_str = request.POST.get('sessie', '')[:7]             # afkappen voor de veiligheid
        klasse_str = request.POST.get('klasse', '')[:7]             # afkappen voor de veiligheid

        try:
            sporterboog_pk = int(sporterboog_str)
            sessie_pk = int(sessie_str)
            klasse_pk = int(klasse_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            sessie = wedstrijd.sessies.get(pk=sessie_pk)
            klasse = wedstrijd.wedstrijdklassen.get(pk=klasse_pk)
            sporterboog = (SporterBoog
                           .objects
                           .select_related('sporter')
                           .exclude(sporter__bij_vereniging=None)
                           .get(pk=sporterboog_pk))
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        # TODO: check wedstrijd geslacht gekozen
        # TODO: check dat klasse bij sporterboog past
        sporter = sporterboog.sporter
        if sporter.is_overleden or not sporter.is_actief_lid or not sporter.bij_vereniging:
            raise Http404('Niet actief lid')

        account_koper = get_account(request)

        now = timezone.now()
        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Handmatig toegevoegd door de HWL: %s\n" % (stamp_str, account_koper.get_account_full_name())

        # maak de inschrijving aan en voorkom dubbelen
        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=klasse,
                            sporterboog=sporterboog,
                            koper=account_koper,
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                            log=msg)

        try:
            with transaction.atomic():
                inschrijving.save()
        except IntegrityError:          # pragma: no cover
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar de achtergrondtaak
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_handmatig_toevoegen_wedstrijd(inschrijving, snel == '1')

        url = reverse('Wedstrijden:aanmeldingen', kwargs={'wedstrijd_pk': wedstrijd.pk})

        return HttpResponseRedirect(url)


# end of file
