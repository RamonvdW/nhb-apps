# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, Http404, UnreadablePostError
from django.views.generic import TemplateView, View
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.contrib.auth.mixins import UserPassesTestMixin
from Account.models import get_account
from Competitie.definities import DEEL_BK, MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV
from Competitie.models import CompetitieIndivKlasse, Kampioenschap, KampioenschapSporterBoog, CompetitieMutatie
from Functie.definities import Rol
from Functie.rol import rol_get_huidige_functie
from Logboek.models import schrijf_in_logboek
from Site.core.background_sync import BackgroundSync
import json


TEMPLATE_COMPBOND_KLEINE_KLASSEN_INDIV = 'complaagbond/kleine-klassen-indiv.dtl'

mutatie_ping = BackgroundSync(settings.BACKGROUND_SYNC__COMPETITIE_MUTATIES)


class KleineKlassenIndivView(UserPassesTestMixin, TemplateView):

    """ Met deze view kan de BKO deelnemers van een kleine individuele klasse
        verplaatsen naar een andere klasse.
    """

    # class variables shared by all instances
    template_name = TEMPLATE_COMPBOND_KLEINE_KLASSEN_INDIV
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            deelkamp_pk = int(kwargs['deelkamp_pk'][:6])  # afkappen voor de veiligheid
            deelkamp = (Kampioenschap
                        .objects
                        .select_related('competitie',
                                        'functie')
                        .get(pk=deelkamp_pk,
                             deel=DEEL_BK))
        except (ValueError, Kampioenschap.DoesNotExist):
            raise Http404('Kampioenschap niet gevonden')

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')

        context['deelkamp'] = deelkamp

        comp = deelkamp.competitie
        comp.bepaal_fase()

        if comp.fase_indiv != 'N':
            raise Http404('Verkeerde competitie fase')

        klassen_cache = dict()      # [klasse.pk] = CompetitieIndivKlasse
        context['klassen'] = alle_klassen = list()
        for klasse in (CompetitieIndivKlasse
                       .objects
                       .filter(competitie=deelkamp.competitie,
                               is_ook_voor_rk_bk=True)
                       .prefetch_related('boogtype')
                       .order_by('volgorde')):
            klassen_cache[klasse.pk] = klasse
            klasse.aantal_deelnemers = 0
            alle_klassen.append(klasse)
        # for

        alle_deelnemers = list()
        klasse = -1
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .select_related('kampioenschap',
                                          'indiv_klasse',
                                          'sporterboog',
                                          'sporterboog__sporter',
                                          'bij_vereniging')
                          .filter(kampioenschap=deelkamp)
                          .order_by('indiv_klasse__volgorde',   # groepeer per klasse
                                    'volgorde',                 # oplopend op volgorde (dubbelen mogelijk)
                                    '-gemiddelde')):            # aflopend op gemiddelde

            deelnemer.break_klasse = (klasse != deelnemer.indiv_klasse.volgorde)
            if deelnemer.break_klasse:
                deelnemer.klasse_str = deelnemer.indiv_klasse.beschrijving
                klasse = deelnemer.indiv_klasse.volgorde

                # volgorde is hoger voor jongere klassen
                volgorde = deelnemer.indiv_klasse.volgorde
                afkorting = deelnemer.indiv_klasse.boogtype.afkorting
                alt_klassen = [klasse for klasse in alle_klassen if klasse.boogtype.afkorting == afkorting and klasse.volgorde < volgorde]
                deelnemer.alt_klassen = alt_klassen
                letter_nr = ord('A')
                for alt_klasse in alt_klassen:
                    alt_klasse.letter = chr(letter_nr)
                    letter_nr += 1
                # for

            klassen_cache[deelnemer.indiv_klasse.pk].aantal_deelnemers += 1

            alle_deelnemers.append(deelnemer)
        # for

        # bepaal de kandidaat-klassen om samen te voegen
        kleine_klassen_pks = list()
        for klasse in alle_klassen:
            if 0 < klasse.aantal_deelnemers < 4:
                klasse.is_klein = True
                kleine_klassen_pks.append(klasse.pk)
        # for

        context['aantal_kleine_klassen'] = len(kleine_klassen_pks)

        context['deelnemers'] = deelnemers = list()
        alt_klassen = list()
        for deelnemer in alle_deelnemers:
            if deelnemer.indiv_klasse.pk in kleine_klassen_pks:
                if deelnemer.break_klasse:
                    alt_klassen = deelnemer.alt_klassen

                deelnemers.append(deelnemer)

                sporter = deelnemer.sporterboog.sporter
                deelnemer.naam_str = "[%s] %s" % (sporter.lid_nr, sporter.volledige_naam())

                deelnemer.wijzig_knoppen = list()
                for alt_klasse in alt_klassen:
                    tup = (alt_klasse.letter, deelnemer.pk, alt_klasse.pk)
                    deelnemer.wijzig_knoppen.append(tup)
                # for
        # for

        context['url_verplaats'] = reverse('CompLaagBond:verplaats-deelnemer')

        context['kruimels'] = (
            (reverse('Competitie:kies'), mark_safe('Bonds<wbr>competities')),
            (reverse('CompBeheer:overzicht', kwargs={'comp_pk': comp.pk}), comp.beschrijving.replace(' competitie', '')),
            (None, 'Kleine klassen individueel')
        )

        return context


class VerplaatsDeelnemerView(UserPassesTestMixin, View):

    """ Met deze view kan de BKO deelnemers van een kleine individuele klasse
        verplaatsen naar een andere klasse.
    """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu == Rol.ROL_BKO

    def post(self, request, *args, **kwargs):

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnreadablePostError):
            # garbage in
            raise Http404('Geen valide verzoek')

        try:
            deelnemer_pk = int(str(data['deelnemer'])[:6])       # afkappen voor de veiligheid
            deelnemer = (KampioenschapSporterBoog
                         .objects
                         .select_related('kampioenschap',
                                         'kampioenschap__functie',
                                         'kampioenschap__competitie',
                                         'indiv_klasse')
                         .get(pk=deelnemer_pk))
        except (KeyError, ValueError, KampioenschapSporterBoog.DoesNotExist):
            raise Http404("Deelnemer niet gevonden")

        deelkamp = deelnemer.kampioenschap

        # controleer dat de juiste BKO aan de knoppen zit
        if self.functie_nu != deelkamp.functie:
            raise PermissionDenied('Niet de beheerder')

        comp = deelkamp.competitie
        comp.bepaal_fase()
        if comp.fase_indiv != 'N':
            raise Http404('Verkeerde competitie fase')

        try:
            klasse_pk = int(str(data['klasse'])[:6])        # afkappen voor de veiligheid
            klasse = (CompetitieIndivKlasse
                      .objects
                      .get(pk=klasse_pk,
                           competitie=comp,
                           is_ook_voor_rk_bk=True))
        except (ValueError, KeyError, CompetitieIndivKlasse.DoesNotExist):
            raise Http404("Klasse niet gevonden")

        account = get_account(request)
        door_str = "BKO %s" % account.volledige_naam()
        door_str = door_str[:149]

        msg = "Kleine klasse %s: deelnemer %s verplaatsen van klasse %s naar klasse %s." % (
                    deelkamp, deelnemer, deelnemer.indiv_klasse.beschrijving, klasse.beschrijving)
        schrijf_in_logboek(account, "Competitie", msg)

        CompetitieMutatie(
                mutatie=MUTATIE_KAMP_VERPLAATS_KLASSE_INDIV,
                door=door_str,
                deelnemer=deelnemer,
                indiv_klasse=klasse).save()

        mutatie_ping.ping()

        out = dict()
        return JsonResponse(out)


# end of file
