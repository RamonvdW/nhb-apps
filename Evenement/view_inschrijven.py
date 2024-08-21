# -*- coding: utf-8 -*-

#  Copyright (c) 2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.db.models import ObjectDoesNotExist
from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Bestel.operations.mandje import mandje_tel_inhoud
from Bestel.operations.mutaties import bestel_mutatieverzoek_inschrijven_evenement
from Evenement.definities import EVENEMENT_INSCHRIJVING_STATUS_DEFINITIEF, EVENEMENT_INSCHRIJVING_STATUS_TO_STR
from Evenement.models import Evenement, EvenementInschrijving
from Functie.definities import Rollen
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Kalender.view_maand import MAAND2URL
from Sporter.models import Sporter, get_sporter
from Sporter.operations import get_sporter_voorkeuren
from datetime import timedelta


TEMPLATE_EVENEMENT_INSCHRIJVEN_SPORTER = 'evenement/inschrijven-sporter.dtl'
TEMPLATE_EVENEMENT_INSCHRIJVEN_GROEPJE = 'evenement/inschrijven-groepje.dtl'
TEMPLATE_EVENEMENT_INSCHRIJVEN_FAMILIE = 'evenement/inschrijven-familie.dtl'
TEMPLATE_EVENEMENT_TOEGEVOEGD_AAN_MANDJE = 'evenement/inschrijven-toegevoegd-aan-mandje.dtl'


def inschrijving_open_of_404(evenement):
    """ Controleer dat het evenement nog open is voor inschrijving.
        Zo niet, genereer dan fout 404
    """

    now_date = timezone.now().date()
    evenement.inschrijven_voor = evenement.datum - timedelta(days=evenement.inschrijven_tot)
    is_voor_sluitingsdatum = now_date < evenement.inschrijven_voor

    if not is_voor_sluitingsdatum:
        raise Http404('Inschrijving is gesloten')


class InschrijvenSporterView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter zichzelf inschrijven voor een evenement """

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_INSCHRIJVEN_SPORTER
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu != Rollen.ROL_NONE

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

        inschrijving_open_of_404(evenement)

        evenement.begrenzing_str = "KHSN leden"

        account = get_account(self.request)
        try:
            lid_nr = int(account.username)
        except ValueError:
            raise Http404('Bondsnummer ontbreekt')

        sporter = (Sporter
                   .objects
                   .exclude(is_overleden=True)
                   .exclude(is_gast=True)         # alleen KHSN leden
                   .filter(lid_nr=lid_nr,
                           is_actief_lid=True)    # moet actief lid zijn
                   .select_related('bij_vereniging')
                   .first())

        if sporter:
            sporter.block_ver = sporter.bij_vereniging.geen_wedstrijden
            context['kan_aanmelden'] = not sporter.block_ver

            context['sporter'] = sporter

            # kijk of de sporter al ingeschreven is
            inschrijving = (EvenementInschrijving
                            .objects
                            .filter(evenement=evenement,
                                    sporter=sporter)
                            .first())
            if inschrijving:
                # sporter is al ingeschreven
                sporter.al_ingeschreven = True
            else:
                sporter.al_ingeschreven = False
                sporter.kan_aanmelden = True

            context['prijs_euro_sporter'] = evenement.bepaal_prijs_voor_sporter(sporter)

        context['url_toevoegen'] = reverse('Evenement:inschrijven-toevoegen-aan-mandje')
        context['menu_toon_mandje'] = True

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': evenement.datum.year,
                                    'maand': MAAND2URL[evenement.datum.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})

        context['kruimels'] = (
            (url_terug, 'Kalender'),
            (reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk}), 'Details evenement'),
            (None, 'Inschrijven sporter')
        )

        return context


class InschrijvenGroepjeView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter een groepje inschrijven voor een evenement"""

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_INSCHRIJVEN_GROEPJE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rollen.ROL_NONE

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

        inschrijving_open_of_404(evenement)

        evenement.begrenzing_str = "KHSN leden"

        try:
            zoek_lid_nr = self.request.GET['bondsnummer']
            zoek_lid_nr = str(zoek_lid_nr)[:6]      # afkappen voor de veiligheid
            zoek_lid_nr = int(zoek_lid_nr)
        except (KeyError, TypeError, ValueError):
            # geen zoekparameter of slechte zoekterm
            zoek_lid_nr = -1
        else:
            # controleer de range
            if not (100000 <= zoek_lid_nr <= 999999):
                zoek_lid_nr = -1

        if zoek_lid_nr != -1:
            sporter = (Sporter
                       .objects
                       .exclude(is_overleden=True)
                       .exclude(bij_vereniging__geen_wedstrijden=True)
                       .exclude(is_gast=True)           # alleen KHSN leden
                       .filter(lid_nr=zoek_lid_nr,
                               is_actief_lid=True)      # moet actief lid zijn
                       .select_related('bij_vereniging')
                       .first())

            if not sporter:
                # niets gevonden
                context['gezocht_niet_gevonden'] = str(zoek_lid_nr)

        else:
            # toon alleen het zoekveld
            sporter = None

        context['sporter'] = sporter

        kan_aanmelden = False
        if sporter:
            # kijk of de sporter al ingeschreven is
            inschrijving = (EvenementInschrijving
                            .objects
                            .filter(evenement=evenement,
                                    sporter=sporter)
                            .first())
            if inschrijving:
                # sporter is al ingeschreven
                sporter.al_ingeschreven = True
            else:
                sporter.al_ingeschreven = False
                sporter.kan_aanmelden = True

            context['prijs_euro_sporter'] = evenement.bepaal_prijs_voor_sporter(sporter)

        context['kan_aanmelden'] = kan_aanmelden
        context['url_toevoegen'] = reverse('Evenement:inschrijven-toevoegen-aan-mandje')
        context['menu_toon_mandje'] = True

        context['url_zoek'] = reverse('Evenement:inschrijven-groepje',
                                      kwargs={'evenement_pk': evenement.pk})

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': evenement.datum.year,
                                    'maand': MAAND2URL[evenement.datum.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})

        context['kruimels'] = (
            (url_terug, 'Kalender'),
            (reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk}), 'Details evenement'),
            (None, 'Inschrijven groepje')
        )

        return context


class InschrijvenFamilieView(UserPassesTestMixin, TemplateView):

    """ Via deze view kan een sporter familie (op hetzelfde adres) inschrijven voor een evenement"""

    # class variables shared by all instances
    template_name = TEMPLATE_EVENEMENT_INSCHRIJVEN_FAMILIE
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rollen.ROL_NONE

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

        inschrijving_open_of_404(evenement)

        evenement.begrenzing_str = "KHSN leden"

        # begrens de mogelijkheden tot leden met dezelfde adres_code als de ingelogde gebruiker
        account = get_account(self.request)
        sporter = get_sporter(account)
        adres_code = sporter.adres_code

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

        context['familie'] = list(Sporter
                                  .objects
                                  .exclude(is_overleden=True)
                                  .exclude(bij_vereniging__geen_wedstrijden=True)
                                  .exclude(is_gast=True)            # alleen KHSN leden
                                  .filter(adres_code=adres_code,
                                          is_actief_lid=True)       # moet actief lid zijn
                                  .select_related('bij_vereniging')
                                  .order_by('sinds_datum',
                                            'lid_nr')[:50])

        context['niets_gevonden'] = True
        geselecteerd = None
        for sporter in context['familie']:
            context['niets_gevonden'] = False

            sporter.is_geselecteerd = False

            sporter.url_selecteer = reverse('Evenement:inschrijven-familie-lid',
                                            kwargs={'evenement_pk': evenement.pk,
                                                    'lid_nr': sporter.lid_nr})

            if sporter.lid_nr == lid_nr:
                geselecteerd = sporter
        # for

        if not geselecteerd and len(context['familie']) > 0:
            geselecteerd = context['familie'][0]

        if geselecteerd:
            context['geselecteerd'] = geselecteerd

            # geen wissel knop meer tonen
            geselecteerd.is_geselecteerd = True
            geselecteerd.url_selecteer = None

            inschrijving = EvenementInschrijving.objects.filter(evenement=evenement, sporter=geselecteerd).first()

            geselecteerd.al_ingeschreven = inschrijving is not None

            geselecteerd.prijs_euro = evenement.bepaal_prijs_voor_sporter(geselecteerd)

        context['menu_toon_mandje'] = True
        context['url_toevoegen'] = reverse('Evenement:inschrijven-toevoegen-aan-mandje')

        url_terug = reverse('Kalender:maand',
                            kwargs={'jaar': evenement.datum.year,
                                    'maand': MAAND2URL[evenement.datum.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})

        context['kruimels'] = (
            (url_terug, 'Kalender'),
            (reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk}), 'Details evenement'),
            (None, 'Inschrijven familie'),
        )

        return context


class ToevoegenAanMandjeView(UserPassesTestMixin, View):

    """ Met deze view wordt het toevoegen van een evenement aan het mandje van de koper afgehandeld """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        rol_nu = rol_get_huidige(self.request)
        return rol_nu != Rollen.ROL_NONE

    def post(self, request, *args, **kwargs):
        evenement_str = request.POST.get('evenement', '')[:6]       # afkappen voor de veiligheid
        sporter_str = request.POST.get('sporter', '')[:6]           # afkappen voor de veiligheid
        goto_str = request.POST.get('goto', '')[:6]                 # afkappen voor de veiligheid

        try:
            evenement_pk = int(evenement_str)
            sporter_pk = int(sporter_str)
        except (ValueError, TypeError):
            raise Http404('Slecht verzoek')

        try:
            evenement = Evenement.objects.get(pk=evenement_pk)
            sporter = (Sporter
                       .objects
                       .exclude(bij_vereniging__geen_wedstrijden=True)
                       .exclude(is_gast=True)           # alleen KHSN leden
                       .select_related('bij_vereniging')
                       .get(pk=sporter_pk))
        except ObjectDoesNotExist:
            raise Http404('Onderdeel van verzoek niet gevonden')

        inschrijving_open_of_404(evenement)

        if sporter.is_overleden or not sporter.is_actief_lid or not sporter.bij_vereniging:
            raise Http404('Niet actief lid')

        account_koper = get_account(request)

        now = timezone.now()
        stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')
        msg = "[%s] Toegevoegd aan het mandje van %s\n" % (stamp_str, account_koper.get_account_full_name())

        # maak de inschrijving aan
        inschrijving = EvenementInschrijving(
                            wanneer=now,
                            evenement=evenement,
                            sporter=sporter,
                            koper=account_koper,
                            log=msg)

        try:
            # voorkom dubbele records
            with transaction.atomic():
                inschrijving.save()
        except IntegrityError:          # pragma: no cover
            # er is niet voldaan aan de uniqueness constraint (sessie, sporterboog)
            # ga uit van user-error (dubbelklik op knop) en skip de rest gewoon
            pass
        else:
            # zet dit verzoek door naar de achtergrondtaak
            snel = str(request.POST.get('snel', ''))[:1]
            bestel_mutatieverzoek_inschrijven_evenement(account_koper, inschrijving, snel == '1')

            mandje_tel_inhoud(self.request)

        # render de pagina "toegevoegd aan mandje"

        context = dict()

        url_maand = reverse('Kalender:maand',
                            kwargs={'jaar': evenement.datum.year,
                                    'maand': MAAND2URL[evenement.datum.month],
                                    'soort': 'alle',
                                    'bogen': 'auto'})

        inschrijven_str = 'Inschrijven'
        url = reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk})

        if goto_str == 'S':
            inschrijven_str += ' Sporter'

        elif goto_str == 'F':
            inschrijven_str += ' Familie'
            # ga terug naar de familie pagina met dezelfde sporter geselecteerd
            url = reverse('Evenement:inschrijven-familie-lid',
                          kwargs={'evenement_pk': evenement.pk,
                                  'lid_nr': sporter.lid_nr})

        else:  # if goto_str == 'G':
            inschrijven_str += ' Groepje'

        context['url_verder'] = url
        context['url_mandje'] = reverse('Bestel:toon-inhoud-mandje')
        context['menu_toon_mandje'] = True

        context['kruimels'] = (
            (url_maand, 'Kalender'),
            (reverse('Evenement:details', kwargs={'evenement_pk': evenement.pk}), 'Details evenement'),
            (url, inschrijven_str),
            (None, 'Toegevoegd aan mandje')
        )

        return render(request, TEMPLATE_EVENEMENT_TOEGEVOEGD_AAN_MANDJE, context)


# end of file
