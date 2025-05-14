# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import UserPassesTestMixin
from BasisTypen.definities import GESLACHT2STR
from Betaal.format import format_bedrag_euro
from Functie.definities import Rol
from Functie.rol import rol_get_huidige, rol_get_huidige_functie
from Sporter.models import SporterVoorkeuren
from Wedstrijden.definities import (WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF,
                                    WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD)
from Wedstrijden.models import Wedstrijd, WedstrijdInschrijving
from Wedstrijden.operations.kwalificatie_scores import get_kwalificatie_scores
from decimal import Decimal
from codecs import BOM_UTF8
import csv


TEMPLATE_WEDSTRIJDEN_AANMELDINGEN = 'wedstrijden/aanmeldingen.dtl'

CONTENT_TYPE_TSV = 'text/tab-separated-values; charset=UTF-8'
CONTENT_TYPE_CSV = 'text/csv; charset=UTF-8'


def get_inschrijving_mh_bestel_nr(inschrijving: WedstrijdInschrijving):
    if inschrijving.bestelling:
        regel = inschrijving.bestelling
        bestelling = regel.bestelling_set.first()
        if bestelling:      # pragma: no branch
            return bestelling.mh_bestel_nr()

    return ""


class WedstrijdAanmeldingenView(UserPassesTestMixin, TemplateView):

    """ Via deze view kunnen beheerders de inschrijvingen voor een wedstrijd inzien """

    # class variables shared by all instances
    template_name = TEMPLATE_WEDSTRIJDEN_AANMELDINGEN
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu = None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu = rol_get_huidige(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def get_context_data(self, **kwargs):
        """ called by the template system to get the context data for the template """
        context = super().get_context_data(**kwargs)

        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        context['wed'] = wedstrijd

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .select_related('sessie',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'pk'))        # = reserveringsnummer
        context['aanmeldingen'] = aanmeldingen

        totaal_ontvangen_euro = Decimal('000.00')
        totaal_retour_euro = Decimal('000.00')

        aantal_aanmeldingen = 0
        aantal_afmeldingen = 0
        for aanmelding in aanmeldingen:

            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter

            if aanmelding.status not in (WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                         WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD):
                aantal_aanmeldingen += 1
                aanmelding.volg_nr = aantal_aanmeldingen
                aanmelding.reserveringsnummer = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD
                aanmelding.is_definitief = (aanmelding.status == WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
            else:
                aantal_afmeldingen += 1
                aanmelding.is_afgemeld = True

            aanmelding.status_str = WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status]

            aanmelding.sporter_str = sporter.lid_nr_en_volledige_naam()
            aanmelding.boog_str = sporterboog.boogtype.beschrijving

            aanmelding.korting_str = 'geen'
            if aanmelding.korting:
                aanmelding.korting_str = '%s%%' % aanmelding.korting.percentage

            aanmelding.url_details = reverse('Wedstrijden:details-aanmelding',
                                             kwargs={'inschrijving_pk': aanmelding.pk})

            totaal_ontvangen_euro += aanmelding.ontvangen_euro
            totaal_retour_euro += aanmelding.retour_euro
        # for

        # context['totaal_euro'] = totaal_ontvangen_euro - totaal_retour_euro
        context['totaal_ontvangen_euro'] = totaal_ontvangen_euro
        context['totaal_retour_euro'] = totaal_retour_euro
        context['aantal_aanmeldingen'] = aantal_aanmeldingen
        context['aantal_afmeldingen'] = aantal_afmeldingen

        context['url_download_tsv'] = reverse('Wedstrijden:download-aanmeldingen-tsv',
                                              kwargs={'wedstrijd_pk': wedstrijd.pk})
        context['url_download_csv'] = reverse('Wedstrijden:download-aanmeldingen-csv',
                                              kwargs={'wedstrijd_pk': wedstrijd.pk})

        if self.rol_nu == Rol.ROL_HWL:
            context['url_toevoegen'] = reverse('WedstrijdInschrijven:inschrijven-handmatig',
                                               kwargs={'wedstrijd_pk': wedstrijd.pk})

        if self.rol_nu == Rol.ROL_HWL:
            context['kruimels'] = (
                (reverse('Vereniging:overzicht'), 'Beheer vereniging'),
                (reverse('Wedstrijden:vereniging'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )
        else:
            # MWZ
            context['kruimels'] = (
                (reverse('Wedstrijden:manager'), 'Wedstrijdkalender'),
                (None, 'Aanmeldingen'),
            )

        return context


class DownloadAanmeldingenBestandTSV(UserPassesTestMixin, View):

    """ Maak een simpel bestand met alle aanmeldingen met tab-gescheiden velden (TSV = tab separated values).
        geschikt voor importeren in een scoreverwerkingsprogramma
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
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def get(self, request, *args, **kwargs):
        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .prefetch_related('sessies')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
                raise Http404('Wedstrijd is niet bij jullie vereniging')

        lid_nr2geslacht = dict()     # [lid_nr] = wedstrijd geslacht (M/V/X)
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            sporter = voorkeuren.sporter

            if voorkeuren.wedstrijd_geslacht_gekozen:
                lid_nr2geslacht[sporter.lid_nr] = voorkeuren.wedstrijd_geslacht
        # for

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                             WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))
                        .select_related('sessie',
                                        'wedstrijdklasse',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'wanneer',
                                  'status'))

        response = HttpResponse(content_type=CONTENT_TYPE_TSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.txt"'

        # Ianseo supports a tab-separated file with specific column order, without headers
        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter="\t")       # tab separated fields

        # maak een mapping van sessie naar nummers 1..n
        sessie_pk2nr = dict()       # [pk] = nr
        nr = 0
        for sessie in wedstrijd.sessies.order_by('pk'):
            nr += 1
            sessie_pk2nr[sessie.pk] = nr
        # for

        for aanmelding in aanmeldingen:
            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter
            sessie_nr = sessie_pk2nr[aanmelding.sessie.pk]
            klasse_afkorting = aanmelding.wedstrijdklasse.afkorting
            ver = sporter.bij_vereniging
            if ver:
                ver_nr = ver.ver_nr
                ver_naam = ver.naam
            else:
                ver_nr = 0
                ver_naam = '?'

            try:
                wedstrijd_geslacht = lid_nr2geslacht[sporter.lid_nr]
            except KeyError:
                # wedstrijdgeslacht is niet bekend
                # neem het geslacht van de sporter zelf
                wedstrijd_geslacht = sporter.geslacht

            writer.writerow([sporter.lid_nr,        # TODO: sporter met meerdere bogen niet ondersteund
                             sessie_nr,
                             sporterboog.boogtype.afkorting,
                             klasse_afkorting,      # wedstrijdklasse zoals gedefinieerd voor de wedstrijd
                             '',                    # baan
                             1,                     # indiv qualification
                             0,                     # team qualification
                             0,                     # indiv finals
                             0,                     # team finals
                             0,                     # mixed finals
                             sporter.achternaam,    # achternaam (wordt oms omgezet in hoofdletters)
                             sporter.voornaam,      # voornaam
                             wedstrijd_geslacht,    # M/0 is man, de rest vrouw
                             ver_nr,
                             ver_naam,
                             sporter.geboorte_datum.strftime('%Y-%m-%d')])
        # for

        return response


class DownloadAanmeldingenBestandCSV(UserPassesTestMixin, View):

    """ Maak een bestand met alle inschrijvingen, geschikt voor import in een spreadsheet programma """

    # class variables shared by all instances
    raise_exception = True      # genereer PermissionDenied als test_func False terug geeft
    permission_denied_message = 'Geen toegang'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rol_nu, self.functie_nu = None, None

    def test_func(self):
        """ called by the UserPassesTestMixin to verify the user has permissions to use this view """
        self.rol_nu, self.functie_nu = rol_get_huidige_functie(self.request)
        return self.rol_nu in (Rol.ROL_HWL, Rol.ROL_MWZ)

    def get(self, request, *args, **kwargs):
        try:
            wedstrijd_pk = str(kwargs['wedstrijd_pk'])[:6]     # afkappen voor de veiligheid
            wedstrijd = (Wedstrijd
                         .objects
                         .select_related('organiserende_vereniging')
                         .get(pk=wedstrijd_pk))
        except (ValueError, TypeError, Wedstrijd.DoesNotExist):
            raise Http404('Wedstrijd niet gevonden')

        if self.rol_nu == Rol.ROL_HWL:
            if wedstrijd.organiserende_vereniging.ver_nr != self.functie_nu.vereniging.ver_nr:
                raise Http404('Wedstrijd is niet bij jullie vereniging')

        lid_nr2voorkeuren = dict()   # [lid_nr] = SporterVoorkeuren
        for voorkeuren in SporterVoorkeuren.objects.select_related('sporter').all():
            sporter = voorkeuren.sporter

            lid_nr2voorkeuren[sporter.lid_nr] = voorkeuren
        # for

        aanmeldingen = (WedstrijdInschrijving
                        .objects
                        .filter(wedstrijd=wedstrijd)
                        .exclude(status__in=(WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD,
                                             WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD))
                        .select_related('sessie',
                                        'wedstrijdklasse',
                                        'sporterboog',
                                        'sporterboog__sporter',
                                        'sporterboog__boogtype',
                                        'korting')
                        .order_by('sessie',
                                  'wanneer',
                                  'status'))

        response = HttpResponse(content_type=CONTENT_TYPE_CSV)
        response['Content-Disposition'] = 'attachment; filename="aanmeldingen.csv"'

        response.write(BOM_UTF8)
        writer = csv.writer(response, delimiter=";")      # ; is good for dutch regional settings

        if wedstrijd.eis_kwalificatie_scores:
            writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Status',
                             'Bestelnummer', 'Prijs', 'Korting', 'Ontvangen', 'Retour',
                             'Sessie', 'Code', 'Wedstrijdklasse',
                             'Lid nr', 'Sporter', 'E-mailadres', 'Geslacht', 'Boog', 'Ver nr', 'Vereniging',
                             'Kwalificatie 180p', 'Kwalificatie 60p', 'Kwalificatie 60p', 'Kwalificatie 60p',
                             'Para classificatie', 'Voorwerpen op schietlijn', 'Para opmerking'])
        else:
            writer.writerow(['Reserveringsnummer', 'Aangemeld op', 'Status',
                             'Bestelnummer', 'Prijs', 'Korting', 'Ontvangen', 'Retour',
                             'Sessie', 'Code', 'Wedstrijdklasse',
                             'Lid nr', 'Sporter', 'E-mailadres', 'Geslacht', 'Boog', 'Ver nr', 'Vereniging',
                             'Para classificatie', 'Voorwerpen op schietlijn', 'Para opmerking'])

        output = list()
        for aanmelding in aanmeldingen:
            sporterboog = aanmelding.sporterboog
            sporter = sporterboog.sporter
            reserveringsnummer = aanmelding.pk + settings.TICKET_NUMMER_START__WEDSTRIJD

            bestelnummer_str = get_inschrijving_mh_bestel_nr(aanmelding)

            if sporter.bij_vereniging:
                ver_nr = sporter.bij_vereniging.ver_nr
                ver_str = sporter.bij_vereniging.naam
            else:
                ver_nr = 0
                ver_str = 'geen'

            # ga uit van het geslacht van de sporter zelf
            wedstrijd_geslacht = sporter.geslacht
            para_materiaal = para_notitie = ''

            try:
                voorkeuren = lid_nr2voorkeuren[sporter.lid_nr]
            except KeyError:
                pass
            else:
                if voorkeuren.para_voorwerpen:
                    para_materiaal = 'Ja'
                para_notitie = voorkeuren.opmerking_para_sporter

                if voorkeuren.wedstrijd_geslacht_gekozen:
                    wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

            regel = aanmelding.bestelling
            if regel:
                bedrag_euro_str = format_bedrag_euro(regel.bedrag_euro)
            else:
                bedrag_euro_str = 'Geen (handmatige inschrijving)'

            if aanmelding.korting:
                korting_str = '%s%%' % aanmelding.korting.percentage
            else:
                korting_str = 'Geen'

            if wedstrijd.eis_kwalificatie_scores:
                # FUTURE: deze individuele queries maken het erg duur (wordt bijna nooit gebruikt)
                scores = get_kwalificatie_scores(aanmelding)

                score1_60p = score2_60p = score3_60p = 0

                if len(scores) >= 1:
                    score1_60p = scores[0].resultaat

                if len(scores) >= 2:
                    score2_60p = scores[1].resultaat

                if len(scores) >= 3:
                    score3_60p = scores[2].resultaat

                score_180p = score1_60p + score2_60p + score3_60p

                row = [
                    str(reserveringsnummer),
                    timezone.localtime(aanmelding.wanneer).strftime('%Y-%m-%d %H:%M'),
                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                    bestelnummer_str,
                    bedrag_euro_str,
                    korting_str,
                    format_bedrag_euro(aanmelding.ontvangen_euro),
                    format_bedrag_euro(aanmelding.retour_euro),
                    aanmelding.sessie.beschrijving,
                    aanmelding.wedstrijdklasse.afkorting,
                    aanmelding.wedstrijdklasse.beschrijving,
                    str(sporter.lid_nr),
                    sporter.volledige_naam(),
                    sporter.email,
                    GESLACHT2STR[wedstrijd_geslacht],
                    sporterboog.boogtype.beschrijving,
                    str(ver_nr),
                    ver_str,
                    score_180p,
                    score1_60p,
                    score2_60p,
                    score3_60p,
                    sporter.para_classificatie,
                    para_materiaal,
                    para_notitie]

                tup = (aanmelding.sessie.datum, aanmelding.sessie.tijd_begin, aanmelding.wedstrijdklasse.afkorting,
                       0 - score_180p, aanmelding.wanneer, aanmelding.pk, row)
            else:
                row = [
                    str(reserveringsnummer),
                    timezone.localtime(aanmelding.wanneer).strftime('%Y-%m-%d %H:%M'),
                    WEDSTRIJD_INSCHRIJVING_STATUS_TO_SHORT_STR[aanmelding.status],
                    bestelnummer_str,
                    bedrag_euro_str,
                    korting_str,
                    format_bedrag_euro(aanmelding.ontvangen_euro),
                    format_bedrag_euro(aanmelding.retour_euro),
                    aanmelding.sessie.beschrijving,
                    aanmelding.wedstrijdklasse.afkorting,
                    aanmelding.wedstrijdklasse.beschrijving,
                    str(sporter.lid_nr),
                    sporter.volledige_naam(),
                    sporter.email,
                    GESLACHT2STR[wedstrijd_geslacht],
                    sporterboog.boogtype.beschrijving,
                    str(ver_nr),
                    ver_str,
                    sporter.para_classificatie,
                    para_materiaal,
                    para_notitie]

                tup = (aanmelding.sessie.datum, aanmelding.sessie.tijd_begin, aanmelding.wedstrijdklasse.afkorting,
                       0, aanmelding.wanneer, aanmelding.pk, row)

            output.append(tup)
        # for

        output.sort()
        for tup in output:
            row = tup[-1]
            writer.writerow(row)
        # for

        return response


# end of file
