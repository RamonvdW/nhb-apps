# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via ScheidsMutatie
"""

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.db.utils import DataError, OperationalError, IntegrityError
from django.core.management.base import BaseCommand
from Account.models import Account
from BasisTypen.definities import SCHEIDS_NIET, SCHEIDS_VERENIGING
from Competitie.models import CompetitieMatch
from Functie.models import Functie
from Locatie.models import Reistijd, WedstrijdLocatie
from Locatie.operations import ReistijdBepalen
from Mailer.operations import mailer_queue_email, render_email_template
from Overig.background_sync import BackgroundSync
from Scheidsrechter.definities import (SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN,
                                       SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_WEDSTRIJD,
                                       SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_MATCH,
                                       SCHEIDS_MUTATIE_COMPETITIE_BESCHIKBAARHEID_OPVRAGEN,
                                       SCHEIDS_MUTATIE_REISTIJD_SR_BEPALEN)
from Scheidsrechter.models import WedstrijdDagScheidsrechters, MatchScheidsrechters, ScheidsMutatie
from Sporter.models import Sporter
from Taken.operations import maak_taak
from Vereniging.models import Vereniging
from Wedstrijden.definities import (WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_BEGRENZING_LANDELIJK,
                                    WEDSTRIJD_DISCIPLINE_INDOOR)
from Wedstrijden.models import Wedstrijd
import traceback
import datetime
import sys


EMAIL_TEMPLATE_BESCHIKBAARHEID_OPGEVEN = 'email_scheidsrechter/beschikbaarheid-opgeven.dtl'
EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_GEKOZEN = 'email_scheidsrechter/voor-wedstrijddag-gekozen.dtl'
EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_NIET_MEER_NODIG = 'email_scheidsrechter/voor-wedstrijddag-niet-meer-nodig.dtl'


def stuur_email_naar_sr_beschikbaarheid_opgeven(wedstrijd: Wedstrijd, datums: list, account: Account, email_cs):
    """ Stuur een e-mail om de beschikbaarheid op te vragen """

    if wedstrijd.aantal_scheids > 0:
        soort_sr = '%s scheidsrechter' % wedstrijd.aantal_scheids
        if wedstrijd.aantal_scheids > 1:
            soort_sr += 's'
    else:
        # uitzonderingssituatie: aantal niet ingevuld (komt voor bij RK/BK)
        soort_sr = 'scheidsrechters'

    if len(datums) > 1:
        zelfde_maand = True
        maand = datums[0].month
        for datum in datums[1:]:
            if datum.month != maand:
                zelfde_maand = False
        # for
        if zelfde_maand:
            # 5 + 6 november 2023
            wed_datums = " + ".join([str(datum.day) for datum in datums])
            wed_datums += date_format(datums[0], " F Y")
        else:
            # 30 november 2023 + 1 december 2023
            wed_datums = " + ".join([date_format(datum, "j F Y") for datum in datums])
    else:
        # 1 november 2023
        wed_datums = date_format(datums[0], "j F Y")

    url = settings.SITE_URL + reverse('Scheidsrechter:beschikbaarheid-wijzigen')

    context = {
        'voornaam': account.get_first_name(),
        'soort_sr': soort_sr,
        'wed_titel': wedstrijd.titel,
        'wed_plaats': wedstrijd.locatie.plaats,
        'wed_datum': wed_datums,
        'email_cs': email_cs,
        'url_beschikbaarheid': url,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_BESCHIKBAARHEID_OPGEVEN)

    mailer_queue_email(account.bevestigde_email,
                       'Beschikbaarheid opgeven voor %s' % wed_datums,
                       mail_body)


def stuur_email_naar_sr_voor_wedstrijddag_gekozen(dag: WedstrijdDagScheidsrechters, sporter: Sporter, email_cs):
    """ Stuur een e-mail om de keuze te melden """

    account = sporter.account
    wedstrijd = dag.wedstrijd
    datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
    wed_datum = date_format(datum, "j F Y")
    wed_adres = wedstrijd.locatie.adres.replace('\r\n', '\n')
    url = settings.SITE_URL + reverse('Scheidsrechter:wedstrijd-details', kwargs={'wedstrijd_pk': wedstrijd.pk})

    context = {
        'voornaam': account.get_first_name(),
        'wed_titel': wedstrijd.titel,
        'wed_datum': wed_datum,
        'wed_ver': wedstrijd.organiserende_vereniging.ver_nr_en_naam(),
        'wed_adres': wed_adres.split('\n'),
        'url_wed_details': url,
        'org_email': wedstrijd.contact_email,
        'org_naam': wedstrijd.contact_naam,
        'org_tel': wedstrijd.contact_telefoon,
        'email_cs': email_cs,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_GEKOZEN)

    mailer_queue_email(account.bevestigde_email,
                       'Geselecteerd voor wedstrijd %s' % wed_datum,
                       mail_body)


def stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig(dag, sporter: Sporter, email_cs):
    """ Stuur een e-mail om de de-keuze te melden """

    account = sporter.account
    wedstrijd = dag.wedstrijd
    datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
    wed_datum = date_format(datum, "j F Y")

    context = {
        'voornaam': account.get_first_name(),
        'wed_titel': wedstrijd.titel,
        'wed_datum': wed_datum,
        'wed_ver': wedstrijd.organiserende_vereniging.ver_nr_en_naam(),
        'email_cs': email_cs,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_NIET_MEER_NODIG)

    mailer_queue_email(account.bevestigde_email,
                       'Niet meer nodig voor wedstrijd %s' % wed_datum,
                       mail_body)


def stuur_email_naar_sr_voor_match_gekozen(match: CompetitieMatch, sporter: Sporter, email_cs):
    """ Stuur een e-mail om de keuze te melden """

    account = sporter.account
    wed_datum = date_format(match.datum_wanneer, "j F Y")
    contact_naam = 'Niet beschikbaar'
    contact_email = 'Onbekend'
    contact_telefoon = 'Onbekend'
    wed_ver = 'Nog niet bekend'

    if match.vereniging:
        wed_ver = match.vereniging.ver_nr_en_naam()
        functie_hwl = match.vereniging.functie_set.filter(rol='HWL').first()
        if functie_hwl:
            if functie_hwl.bevestigde_email:
                contact_email = functie_hwl.bevestigde_email
            if functie_hwl.telefoon:
                contact_telefoon = functie_hwl.telefoon
            account_hwl = functie_hwl.accounts.first()
            if account_hwl:
                contact_naam = account_hwl.volledige_naam()

    if match.locatie:
        wed_adres = match.locatie.adres.replace('\r\n', '\n')
    else:
        wed_adres = 'Nog niet bekend'

    url = settings.SITE_URL + reverse('Scheidsrechter:match-details', kwargs={'match_pk': match.pk})

    context = {
        'voornaam': account.get_first_name(),
        'wed_titel': match.beschrijving,
        'wed_datum': wed_datum,
        'wed_ver': wed_ver,
        'wed_adres': wed_adres.split('\n'),
        'url_wed_details': url,
        'org_email': contact_email,
        'org_naam': contact_naam,
        'org_tel': contact_telefoon,
        'email_cs': email_cs,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_GEKOZEN)

    mailer_queue_email(account.bevestigde_email,
                       'Geselecteerd voor wedstrijd %s' % wed_datum,
                       mail_body)


def stuur_email_naar_sr_voor_match_niet_meer_nodig(match: CompetitieMatch, sporter: Sporter, email_cs):
    """ Stuur een e-mail om de de-keuze te melden """

    account = sporter.account
    wed_datum = date_format(match.datum_wanneer, "j F Y")
    wed_ver = 'Nog niet bekend'
    if match.vereniging:
        wed_ver = match.vereniging.ver_nr_en_naam()

    context = {
        'voornaam': account.get_first_name(),
        'wed_titel': match.beschrijving,
        'wed_datum': wed_datum,
        'wed_ver': wed_ver,
        'email_cs': email_cs,
    }

    mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_NIET_MEER_NODIG)

    mailer_queue_email(account.bevestigde_email,
                       'Niet meer nodig voor wedstrijd %s' % wed_datum,
                       mail_body)


class Command(BaseCommand):

    help = "Scheidsrechter mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__SCHEIDS_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

        functie_cs = Functie.objects.get(rol='CS')
        self._email_cs = functie_cs.bevestigde_email

        ver_nr = settings.WEDSTRIJDEN_KIES_UITVOERENDE_VERENIGING[0]
        self.ver_bondsbureau = Vereniging.objects.get(ver_nr=ver_nr)

        loc, is_created = WedstrijdLocatie.objects.get_or_create(naam='Placeholder RK/BK voor SR',
                                                                 zichtbaar=False,
                                                                 discipline_indoor=True,
                                                                 adres='(diverse)',
                                                                 plaats='(diverse)',
                                                                 notities='Automatisch aangemaakt voor opvragen SR naar RK/BK')
        if is_created:
            loc.verenigingen.add(self.ver_bondsbureau)
        self.locatie_placeholder = loc

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices=(1, 2, 5, 7, 10, 15, 20, 30, 45, 60),
                            help="Maximum aantal minuten actief blijven")
        parser.add_argument('--stop_exactly', type=int, default=None, choices=range(60),
                            help="Stop op deze minuut")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _reistijd_opvragen(self, locatie, sporter):
        """ vraag de reistijd op tussen de postcode van de sporter/scheidsrechter en de locatie """

        # nieuwe verzoeken worden door het management commando "reistijd berekenen" verwerkt
        if sporter.adres_lat and sporter.adres_lon:
            _ = Reistijd.objects.get_or_create(
                                    vanaf_lat=sporter.adres_lat,
                                    vanaf_lon=sporter.adres_lon,
                                    naar_lat=locatie.adres_lat,
                                    naar_lon=locatie.adres_lon)
            # wordt later verwerkt (door een achtergrondtaak)
        else:
            self.stdout.write('[WARNING] Nog geen lat/lon bekend voor sporter %s' % sporter.lid_nr)

    def _verwerk_mutatie_beschikbaarheid_opvragen_wedstrijd(self, mutatie):
        wedstrijd = mutatie.wedstrijd
        self.stdout.write('[INFO] Beschikbaarheid %s SR opvragen voor wedstrijd %s' % (wedstrijd.aantal_scheids,
                                                                                       wedstrijd))

        vraag = list()
        aantal_dagen = (wedstrijd.datum_einde - wedstrijd.datum_begin).days + 1
        for dag_nr in range(aantal_dagen):
            _, is_new = (WedstrijdDagScheidsrechters
                         .objects
                         .get_or_create(wedstrijd=wedstrijd,
                                        dag_offset=dag_nr))

            if is_new:
                # voor deze dag een verzoek versturen
                datum = wedstrijd.datum_begin + datetime.timedelta(days=dag_nr)
                vraag.append(datum)
        # for

        # doorloop alle scheidsrechters
        qset = Sporter.objects.exclude(scheids=SCHEIDS_NIET)

        qset = qset.exclude(lid_nr__in=settings.LID_NRS_GEEN_SCHEIDS_BESCHIKBAARHEID_OPVRAGEN)

        # alleen SR's hanteren die een account aangemaakt hebben
        qset = qset.exclude(account=None)

        # alleen een hoofdscheidsrechter nodig? --> dan niet SR3 vragen
        if wedstrijd.aantal_scheids <= 1:
            qset = qset.exclude(scheids=SCHEIDS_VERENIGING)

        for sporter in qset:

            # reisafstand laten berekenen voor deze SR
            self._reistijd_opvragen(wedstrijd.locatie, sporter)

            # stuur een e-mail
            if len(vraag):
                # minimaal 1 datum
                stuur_email_naar_sr_beschikbaarheid_opgeven(wedstrijd, vraag, sporter.account, self._email_cs)
        # for

        # verwerk de nieuwe verzoeken voor reistijd
        bepaler = ReistijdBepalen(self.stdout, self.stderr)
        bepaler.run()

    def _adjust_rk_bk_datum_reeks(self, wedstrijd, alle_datums):
        self.stdout.write('[WARNING] Wijziging RK/BK datum reeks: datum_begin: %s --> %s; datum_einde: %s --> %s' % (
                            wedstrijd.datum_begin, alle_datums[0],
                            wedstrijd.datum_einde, alle_datums[-1]))

        # maak mapping bestaande WedstrijdDagScheidsrechters naar datum
        datum2dag_sr = dict()
        for obj in WedstrijdDagScheidsrechters.objects.filter(wedstrijd=wedstrijd):
            datum = wedstrijd.datum_begin + datetime.timedelta(days=obj.dag_offset)
            datum2dag_sr[datum] = obj
        # for

        # pas de wedstrijd aan
        wedstrijd.datum_begin = alle_datums[0]
        wedstrijd.datum_einde = alle_datums[-1]
        wedstrijd.save(update_fields=['datum_begin', 'datum_einde'])

        # zet nieuwe offsets
        for datum in alle_datums:
            try:
                obj = datum2dag_sr[datum]
            except KeyError:
                # bestaat nog niet; wordt later aangemaakt
                pass
            else:
                # pas de dag_offset aantal
                dag_nr = (datum - wedstrijd.datum_begin).days
                self.stdout.write('[DEBUG] Aanpassing dag_offset van %s naar %s for pk=%s' % (obj.dag_offset,
                                                                                              dag_nr,
                                                                                              obj.pk))
                obj.dag_offset = dag_nr
                obj.save(update_fields=['dag_offset'])
        # for

    @staticmethod
    def _maak_competitie_wedstrijddagscheidsrechters(wedstrijd, alle_datums):
        datum2dag_sr = dict()
        for obj in WedstrijdDagScheidsrechters.objects.filter(wedstrijd=wedstrijd):
            datum = wedstrijd.datum_begin + datetime.timedelta(days=obj.dag_offset)
            datum2dag_sr[datum] = obj
        # for

        bulk = list()
        for datum in alle_datums:
            try:
                _ = datum2dag_sr[datum]
            except KeyError:
                # bestaat nog niet
                dag_offset = (datum - wedstrijd.datum_begin).days
                dag_sr = WedstrijdDagScheidsrechters(wedstrijd=wedstrijd,
                                                     dag_offset=dag_offset)
                bulk.append(dag_sr)
        # for

        if len(bulk):
            WedstrijdDagScheidsrechters.objects.bulk_create(bulk)

    def _verwerk_mutatie_beschikbaarheid_opvragen_competitie(self, mutatie):
        """ maak een placeholder Wedstrijd aan voor de RK en BK matches van de competitie;
            als er datumreeks van de wedstrijd niet meer klopt, pas deze dan aan;
            maak een MatchScheidsrechter record aan voor elke CompetitieMatch
        """

        self.stdout.write('[INFO] Beschikbaarheid SR opvragen voor de competitie')

        dit_jaar = timezone.make_aware(datetime.datetime(year=timezone.now().year, month=1, day=1))

        matches = (CompetitieMatch
                   .objects
                   .exclude(aantal_scheids__lt=1)
                   .filter(datum_wanneer__gte=dit_jaar)
                   .order_by('datum_wanneer',       # oudste bovenaan
                             'beschrijving'))       # want veel dezelfde datum

        alle_rk_datums = list()
        alle_bk_datums = list()

        een_match = None

        for match in matches:
            een_match = match
            if match.beschrijving.startswith('BK'):
                if match.datum_wanneer not in alle_bk_datums:
                    alle_bk_datums.append(match.datum_wanneer)
            else:
                if match.datum_wanneer not in alle_rk_datums:
                    alle_rk_datums.append(match.datum_wanneer)

            # maak een MatchScheidsrechter record aan
            match_sr, _ = MatchScheidsrechters.objects.get_or_create(match=match)
        # for

        pos = een_match.beschrijving.find(', ')
        if pos < 0:
            pos = 0
        titel = ' wedstrijden' + een_match.beschrijving[pos:]

        if len(alle_rk_datums) > 0:
            vraag = list()
            rk_titel = 'RK' + titel
            try:
                rk_wedstrijd = Wedstrijd.objects.get(titel=rk_titel)
            except Wedstrijd.DoesNotExist:
                rk_wedstrijd, _ = Wedstrijd.objects.get_or_create(titel=rk_titel,
                                                                  toon_op_kalender=False, verstop_voor_mwz=True,
                                                                  datum_begin=alle_rk_datums[0],
                                                                  datum_einde=alle_rk_datums[-1],
                                                                  organiserende_vereniging=self.ver_bondsbureau,
                                                                  locatie=self.locatie_placeholder,
                                                                  discipline=WEDSTRIJD_DISCIPLINE_INDOOR,
                                                                  begrenzing=WEDSTRIJD_BEGRENZING_LANDELIJK,
                                                                  status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                                                  aantal_scheids=7)        # per dag
                # voor alle datums moeten we een verzoek moeten sturen
                vraag.extend(alle_rk_datums)
            else:
                # check the datums en pas de wedstrijd eventueel aan
                if rk_wedstrijd.datum_begin != alle_rk_datums[0] or rk_wedstrijd.datum_einde != alle_rk_datums[-1]:

                    # zoek uit voor welke datums we een verzoek moeten sturen
                    for datum in alle_rk_datums:
                        if not (rk_wedstrijd.datum_begin <= datum <= rk_wedstrijd.datum_einde):
                            vraag.append(datum)
                    # for

                    self._adjust_rk_bk_datum_reeks(rk_wedstrijd, alle_rk_datums)

            if len(vraag) and rk_wedstrijd.datum_einde > timezone.now().date():
                datums_str = ", ".join(datum.strftime('%Y-%m-%d') for datum in vraag)
                self.stdout.write('[INFO] Vraag beschikbaarheid op voor RK datums: %s' % datums_str)

                self._maak_competitie_wedstrijddagscheidsrechters(rk_wedstrijd, alle_rk_datums)

                # doorloop alle scheidsrechters
                qset = Sporter.objects.exclude(scheids=SCHEIDS_NIET)

                qset = qset.exclude(lid_nr__in=settings.LID_NRS_GEEN_SCHEIDS_BESCHIKBAARHEID_OPVRAGEN)

                # alleen SR's hanteren die een account aangemaakt hebben
                qset = qset.exclude(account=None)

                for sporter in qset:
                    # stuur een e-mail
                    stuur_email_naar_sr_beschikbaarheid_opgeven(rk_wedstrijd, vraag, sporter.account, self._email_cs)
                # for
        del alle_rk_datums

        if len(alle_bk_datums) > 0:
            vraag = list()
            bk_titel = 'BK' + titel
            try:
                bk_wedstrijd = Wedstrijd.objects.get(titel=bk_titel)
            except Wedstrijd.DoesNotExist:
                bk_wedstrijd, _ = Wedstrijd.objects.get_or_create(titel=bk_titel,
                                                                  toon_op_kalender=False, verstop_voor_mwz=True,
                                                                  datum_begin=alle_bk_datums[0],
                                                                  datum_einde=alle_bk_datums[-1],
                                                                  organiserende_vereniging=self.ver_bondsbureau,
                                                                  locatie=self.locatie_placeholder,
                                                                  discipline=WEDSTRIJD_DISCIPLINE_INDOOR,
                                                                  begrenzing=WEDSTRIJD_BEGRENZING_LANDELIJK,
                                                                  status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                                                                  aantal_scheids=6)        # per dag
                # voor alle datums moeten we een verzoek moeten sturen
                vraag.extend(alle_bk_datums)
            else:
                # check the datums
                if bk_wedstrijd.datum_begin != alle_bk_datums[0] or bk_wedstrijd.datum_einde != alle_bk_datums[-1]:

                    # zoek uit voor welke datums we een verzoek moeten sturen
                    for datum in alle_bk_datums:
                        if not (bk_wedstrijd.datum_begin <= datum <= bk_wedstrijd.datum_einde):
                            vraag.append(datum)
                    # for

                    self._adjust_rk_bk_datum_reeks(bk_wedstrijd, alle_bk_datums)

            if len(vraag) and bk_wedstrijd.datum_einde > timezone.now().date():
                datums_str = ", ".join(datum.strftime('%Y-%m-%d') for datum in vraag)
                self.stdout.write('[INFO] Vraag beschikbaarheid op voor BK datums: %s' % datums_str)

                self._maak_competitie_wedstrijddagscheidsrechters(bk_wedstrijd, alle_bk_datums)

                # doorloop alle scheidsrechters
                qset = Sporter.objects.exclude(scheids=SCHEIDS_NIET)

                qset = qset.exclude(lid_nr__in=settings.LID_NRS_GEEN_SCHEIDS_BESCHIKBAARHEID_OPVRAGEN)

                # alleen SR's hanteren die een account aangemaakt hebben
                qset = qset.exclude(account=None)

                for sporter in qset:
                    # stuur een e-mail
                    stuur_email_naar_sr_beschikbaarheid_opgeven(bk_wedstrijd, vraag, sporter.account, self._email_cs)
                # for

    def _maak_taak_hwl_voor_wedstrijd(self, wedstrijd: Wedstrijd):
        self.stdout.write('[INFO] Maak taak voor HWL %s voor wedstrijd pk=%s' % (
                          wedstrijd.organiserende_vereniging.ver_nr, wedstrijd.pk))

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_tekst = "Scheidsrechters zijn geselecteerd.\n\n"

        taak_tekst += "Er is een wijziging doorgevoerd voor de volgende wedstrijd:\n"
        taak_tekst += "Titel: %s\n" % wedstrijd.titel

        datum_str = wedstrijd.datum_begin.strftime('%Y-%m-%d')
        taak_tekst += "Datum: %s\n" % datum_str

        taak_tekst += "\nOnder Wedstrijden kan je de namen en contactgegevens inzien."

        taak_onderwerp = "Scheidsrechters zijn geselecteerd"

        # maak een taak aan voor de HWL van de organiserende vereniging
        functie_hwl = wedstrijd.organiserende_vereniging.functie_set.filter(rol='HWL').first()
        if functie_hwl:  # pragma: no branch
            maak_taak(
                toegekend_aan_functie=functie_hwl,
                deadline=taak_deadline,
                onderwerp=taak_onderwerp,
                beschrijving=taak_tekst,
                log=taak_log)
        else:
            self.stderr.write('[ERROR] HWL functie niet gevonden!')

    def _maak_taak_hwl_voor_match(self, match: CompetitieMatch):
        if not match.vereniging:
            return

        self.stdout.write('[INFO] Maak taak voor HWL %s voor competitie match pk=%s' % (
                          match.vereniging.ver_nr, match.pk))

        now = timezone.now()
        stamp_str = timezone.localtime(now).strftime('%Y-%m-%d om %H:%M')
        taak_deadline = now + datetime.timedelta(days=3)
        taak_log = "[%s] Taak aangemaakt" % stamp_str
        taak_tekst = "Scheidsrechters zijn geselecteerd.\n\n"

        taak_tekst += "Er is een wijziging doorgevoerd voor de volgende wedstrijd:\n"
        taak_tekst += "Titel: %s\n" % match.beschrijving

        datum_str = match.datum_wanneer.strftime('%Y-%m-%d')
        taak_tekst += "Datum: %s\n" % datum_str

        taak_tekst += "\nOnder Competitie Wedstrijden kan je de namen en contactgegevens inzien."

        taak_onderwerp = "Scheidsrechters zijn geselecteerd"

        # maak een taak aan voor de HWL van de organiserende vereniging
        functie_hwl = match.vereniging.functie_set.filter(rol='HWL').first()
        if functie_hwl:  # pragma: no branch
            maak_taak(
                toegekend_aan_functie=functie_hwl,
                deadline=taak_deadline,
                onderwerp=taak_onderwerp,
                beschrijving=taak_tekst,
                log=taak_log)
        else:
            self.stderr.write('[ERROR] HWL functie niet gevonden!')

    def _verwerk_mutatie_stuur_notificaties_wedstrijd(self, mutatie):
        wedstrijd = mutatie.wedstrijd

        when_str = timezone.localtime(mutatie.when).strftime('%Y-%m-%d om %H:%M')

        notify_hwl = False

        for dag in (WedstrijdDagScheidsrechters
                    .objects
                    .filter(wedstrijd=wedstrijd)
                    .select_related('wedstrijd',
                                    'gekozen_hoofd_sr',
                                    'gekozen_sr1', 'gekozen_sr2', 'gekozen_sr3', 'gekozen_sr4', 'gekozen_sr5',
                                    'gekozen_sr6', 'gekozen_sr7', 'gekozen_sr8', 'gekozen_sr9')):

            dag.notified_laatste = '%s door %s' % (when_str, mutatie.door)
            dag.save(update_fields=['notified_laatste'])

            notified_pks = list(dag.notified_srs.all().values_list('pk', flat=True))

            for sporter in (dag.gekozen_hoofd_sr, dag.gekozen_sr1, dag.gekozen_sr2, dag.gekozen_sr3, dag.gekozen_sr4,
                            dag.gekozen_sr5, dag.gekozen_sr6, dag.gekozen_sr7, dag.gekozen_sr8, dag.gekozen_sr9):
                if sporter:
                    if sporter.pk in notified_pks:
                        # sporter heeft al eens een berichtje gehad, dus deze kunnen we overslaan
                        notified_pks.remove(sporter.pk)
                    else:
                        # sporter is nieuw gekozen en moet een berichtje krijgen
                        self.stdout.write('[INFO] Stuur e-mail naar SR %s: voor wedstrijd gekozen' % sporter.lid_nr)

                        if not sporter.account:
                            self.stderr.write(
                                '[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
                        else:
                            stuur_email_naar_sr_voor_wedstrijddag_gekozen(dag, sporter, self._email_cs)
                            dag.notified_srs.add(sporter)
                            notify_hwl = True
            # for

            # alle overgebleven srs zijn niet meer gekozen en kunnen dus een afmelding krijgen
            for sporter in Sporter.objects.filter(pk__in=notified_pks):
                self.stdout.write('[INFO] Stuur e-mail naar SR %s: voor wedstrijd niet meer nodig' % sporter.lid_nr)
                if not sporter.account:
                    self.stderr.write(
                        '[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
                else:
                    stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig(dag, sporter, self._email_cs)
                    dag.notified_srs.remove(sporter)
                    notify_hwl = True
            # for
        # for

        # maak een taak voor de HWL van de organiserende vereniging
        if notify_hwl:
            self._maak_taak_hwl_voor_wedstrijd(wedstrijd)

    def _verwerk_mutatie_stuur_notificaties_competitie(self, mutatie):
        match = mutatie.match

        when_str = timezone.localtime(mutatie.when).strftime('%Y-%m-%d om %H:%M')

        notify_hwl = False

        match_sr = (MatchScheidsrechters
                    .objects
                    .filter(match=match)
                    .select_related('gekozen_hoofd_sr',
                                    'gekozen_sr1',
                                    'gekozen_sr2')
                    ).first()

        if match_sr:
            match_sr.notified_laatste = '%s door %s' % (when_str, mutatie.door)
            match_sr.save(update_fields=['notified_laatste'])

            notified_pks = list(match_sr.notified_srs.all().values_list('pk', flat=True))

            for sporter in (match_sr.gekozen_hoofd_sr, match_sr.gekozen_sr1, match_sr.gekozen_sr2):
                if sporter:
                    if sporter.pk in notified_pks:
                        # sporter heeft al eens een berichtje gehad, dus deze kunnen we overslaan
                        notified_pks.remove(sporter.pk)
                    else:
                        # sporter is nieuw gekozen en moet een berichtje krijgen
                        self.stdout.write(
                            '[INFO] Stuur e-mail naar SR %s: voor competitie match gekozen' % sporter.lid_nr)

                        if not sporter.account:
                            self.stderr.write(
                                '[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
                        else:
                            stuur_email_naar_sr_voor_match_gekozen(match, sporter, self._email_cs)
                            match_sr.notified_srs.add(sporter)
                            notify_hwl = True
            # for

            # alle overgebleven srs zijn niet meer gekozen en kunnen dus een afmelding krijgen
            for sporter in Sporter.objects.filter(pk__in=notified_pks):
                self.stdout.write(
                    '[INFO] Stuur e-mail naar SR %s: voor competitie match niet meer nodig' % sporter.lid_nr)

                if not sporter.account:
                    self.stderr.write(
                        '[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
                else:
                    stuur_email_naar_sr_voor_match_niet_meer_nodig(match, sporter, self._email_cs)
                    match_sr.notified_srs.remove(sporter)
                    notify_hwl = True
            # for
        # for

        # maak een taak voor de HWL van de organiserende vereniging
        if notify_hwl:
            self._maak_taak_hwl_voor_match(match)

    def _verwerk_mutatie_reistijd_scheidsrechters_bepalen(self):
        # bepaal de reisafstand voor alle scheidsrechters naar alle wedstrijdlocaties die in gebruik zijn,
        # inclusief bondscompetitie RK/BK (voor zover nog niet bekend)

        self.stdout.write('[INFO] Reistijd scheidsrechters opvragen naar locatie wedstrijden / Indoor RK/BK')

        date_now = timezone.now().date()

        # reistijd opvragen naar locaties van toekomstige wedstrijden
        for wedstrijd in (Wedstrijd
                          .objects
                          .filter(datum_einde__gte=date_now,
                                  aantal_scheids__gte=1)
                          .exclude(locatie=None)
                          .exclude(locatie__plaats='(diverse)')     # niet specifiek genoeg
                          .select_related('locatie')):

            locatie = wedstrijd.locatie

            for scheids in Sporter.objects.exclude(scheids=SCHEIDS_NIET):
                self._reistijd_opvragen(locatie, scheids)
            # for
        # for

        # reistijd opvragen naar locaties van toekomstige bondscompetities Indoor RK/BK matches
        for match in (CompetitieMatch
                      .objects
                      .filter(competitie__afstand=18,
                              aantal_scheids__gte=1)
                      .exclude(locatie=None)
                      .select_related('locatie')):

            locatie = match.locatie

            for scheids in Sporter.objects.exclude(scheids=SCHEIDS_NIET):
                self._reistijd_opvragen(locatie, scheids)
            # for
        # for

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.mutatie

        if code == SCHEIDS_MUTATIE_WEDSTRIJD_BESCHIKBAARHEID_OPVRAGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Beschikbaarheid opvragen' % mutatie.pk)
            self._verwerk_mutatie_beschikbaarheid_opvragen_wedstrijd(mutatie)

        elif code == SCHEIDS_MUTATIE_COMPETITIE_BESCHIKBAARHEID_OPVRAGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Beschikbaarheid competitie opvragen' % mutatie.pk)
            self._verwerk_mutatie_beschikbaarheid_opvragen_competitie(mutatie)

        elif code == SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_WEDSTRIJD:
            self.stdout.write('[INFO] Verwerk mutatie %s: Notificaties sturen voor wedstrijd' % mutatie.pk)
            self._verwerk_mutatie_stuur_notificaties_wedstrijd(mutatie)

        elif code == SCHEIDS_MUTATIE_STUUR_NOTIFICATIES_MATCH:
            self.stdout.write('[INFO] Verwerk mutatie %s: Notificaties sturen voor competitie match' % mutatie.pk)
            self._verwerk_mutatie_stuur_notificaties_competitie(mutatie)

        elif code == SCHEIDS_MUTATIE_REISTIJD_SR_BEPALEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Reistijd bepalen voor scheidsrechters' % mutatie.pk)
            self._verwerk_mutatie_reistijd_scheidsrechters_bepalen()

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        """ Deze routine wordt aangeroepen als het aantal mutaties in de database gewijzigd is """
        begin = datetime.datetime.now()

        try:
            mutatie_latest = ScheidsMutatie.objects.latest('pk')
        except ScheidsMutatie.DoesNotExist:             # pragma: no cover
            # alle mutatie records zijn verwijderd
            return
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:        # staat initieel op None        # pragma: no cover
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste ScheidsMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (ScheidsMutatie
                    .objects
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (ScheidsMutatie
                    .objects
                    .all())         # deferred

        mutatie_pks = qset.exclude(is_verwerkt=True).order_by('pk').values_list('pk', flat=True)     # deferred

        self._hoogste_mutatie_pk = mutatie_latest.pk

        for pk in mutatie_pks:
            # we halen de records hier 1 voor 1 op
            # zodat we verse informatie hebben inclusief de vorige mutatie
            # en zodat we 1 plek hebben voor select/prefetch
            mutatie = (ScheidsMutatie
                       .objects
                       .select_related('wedstrijd',
                                       'wedstrijd__locatie')
                       .get(pk=pk))

            if not mutatie.is_verwerkt:             # pragma: no branch
                self._verwerk_mutatie(mutatie)

                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
        # for

        self.stdout.write('[INFO] nieuwe hoogste ScheidsMutatie pk is %s' % self._hoogste_mutatie_pk)

        klaar = datetime.datetime.now()
        self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = ScheidsMutatie.objects.count()
            if new_count != mutatie_count:
                mutatie_count = new_count
                self._verwerk_nieuwe_mutaties()
                now = datetime.datetime.now()

            # wacht 5 seconden voordat we opnieuw in de database kijken
            # het wachten kan onderbroken worden door een ping, als er een nieuwe mutatie toegevoegd is
            secs = (self.stop_at - now).total_seconds()
            if secs > 1:                                    # pragma: no branch
                timeout = min(5.0, secs)
                if self._sync.wait_for_ping(timeout):       # pragma: no branch
                    self._count_ping += 1                   # pragma: no cover
            else:
                # near the end
                break       # from the while                # pragma: no cover

            now = datetime.datetime.now()
        # while

    def _set_stop_time(self, **options):
        # bepaal wanneer we moeten stoppen (zoals gevraagd)
        duration = options['duration']
        stop_minute = options['stop_exactly']

        now = datetime.datetime.now()
        self.stop_at = now + datetime.timedelta(minutes=duration)

        if isinstance(stop_minute, int):
            delta = stop_minute - now.minute
            if delta < 0:
                delta += 60
            if delta != 0:    # avoid stopping in start minute
                stop_at_exact = now + datetime.timedelta(minutes=delta)
                stop_at_exact -= datetime.timedelta(seconds=self.stop_at.second,
                                                    microseconds=self.stop_at.microsecond)
                self.stdout.write('[INFO] Calculated stop at is %s' % stop_at_exact)
                if stop_at_exact < self.stop_at:
                    # run duration passes the requested stop minute
                    self.stop_at = stop_at_exact

        # test moet snel stoppen dus interpreteer duration in seconden
        if options['quick']:        # pragma: no branch
            self.stop_at = (datetime.datetime.now()
                            + datetime.timedelta(seconds=duration))

        self.stdout.write('[INFO] Taak loopt tot %s' % str(self.stop_at))

    def handle(self, *args, **options):

        self._set_stop_time(**options)

        # vang generieke fouten af
        try:
            self._monitor_nieuwe_mutaties()
        except (DataError, OperationalError, IntegrityError) as exc:  # pragma: no cover
            _, _, tb = sys.exc_info()
            lst = traceback.format_tb(tb)
            self.stderr.write('[ERROR] Onverwachte database fout: %s' % str(exc))
            self.stderr.write('Traceback:')
            self.stderr.write(''.join(lst))
        except KeyboardInterrupt:                       # pragma: no cover
            pass

        self.stdout.write('[DEBUG] Aantal pings ontvangen: %s' % self._count_ping)

        self.stdout.write('Klaar')


"""
    performance debug helper:

    from django.db import connection

        q_begin = len(connection.queries)

        # queries here

        print('queries: %s' % (len(connection.queries) - q_begin))
        for obj in connection.queries[q_begin:]:
            print('%10s %s' % (obj['time'], obj['sql'][:200]))
        # for
        sys.exit(1)

    test uitvoeren met DEBUG=True via --settings=SiteMain.settings_dev anders wordt er niets bijgehouden
"""

# end of file
