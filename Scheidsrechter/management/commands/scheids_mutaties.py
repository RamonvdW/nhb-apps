# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
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
from Functie.models import Functie
from Locatie.models import Reistijd
from Mailer.operations import mailer_queue_email, render_email_template
from Overig.background_sync import BackgroundSync
from Scheidsrechter.definities import SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN, SCHEIDS_MUTATIE_STUUR_NOTIFICATIES
from Scheidsrechter.models import WedstrijdDagScheidsrechters, ScheidsMutatie
from Sporter.models import Sporter
from Wedstrijden.models import Wedstrijd
import traceback
import datetime
import sys


EMAIL_TEMPLATE_BESCHIKBAARHEID_OPGEVEN = 'email_scheidsrechter/beschikbaarheid-opgeven.dtl'
EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_GEKOZEN = 'email_scheidsrechter/voor-wedstrijddag-gekozen.dtl'
EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_NIET_MEER_NODIG = 'email_scheidsrechter/voor-wedstrijddag-niet-meer-nodig.dtl'


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

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices=(1, 2, 5, 7, 10, 15, 20, 30, 45, 60),
                            help="Maximum aantal minuten actief blijven")
        parser.add_argument('--stop_exactly', type=int, default=None, choices=range(60),
                            help="Stop op deze minuut")
        parser.add_argument('--quick', action='store_true')     # for testing

    def stuur_email_naar_sr_beschikbaarheid_opgeven(self, wedstrijd: Wedstrijd, datums: list, account: Account):
        """ Stuur een e-mail om de beschikbaarheid op te vragen """

        soort_sr = '%s scheidsrechter' % wedstrijd.aantal_scheids
        if wedstrijd.aantal_scheids > 1:
            soort_sr += 's'

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

        url = settings.SITE_URL + reverse('Scheidsrechter:overzicht')

        context = {
            'voornaam': account.get_first_name(),
            'soort_sr': soort_sr,
            'wed_titel': wedstrijd.titel,
            'wed_plaats': wedstrijd.locatie.plaats,
            'wed_datum': wed_datums,
            'email_cs': self._email_cs,
            'url_beschikbaarheid': url,
        }

        mail_body = render_email_template(context, EMAIL_TEMPLATE_BESCHIKBAARHEID_OPGEVEN)

        mailer_queue_email(account.bevestigde_email,
                           'Beschikbaarheid opgeven voor %s' % wed_datums,
                           mail_body)

    def stuur_email_naar_sr_voor_wedstrijddag_gekozen(self, dag: WedstrijdDagScheidsrechters, sporter: Sporter):
        """ Stuur een e-mail om de keuze te melden """

        self.stdout.write('[INFO] Stuur e-mail naar SR %s: voor wedstrijd gekozen' % sporter.lid_nr)

        if not sporter.account:
            self.stderr.write('[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
            return

        account = sporter.account
        wedstrijd = dag.wedstrijd

        datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
        wed_datum = date_format(datum, "j F Y")

        wed_adres = wedstrijd.locatie.adres.replace('\r\n', '\n')

        context = {
            'voornaam': account.get_first_name(),

            'wed_titel': wedstrijd.titel,
            'wed_datum': wed_datum,
            'wed_adres': wed_adres.split('\n'),

            'org_email': wedstrijd.contact_email,
            'org_naam': wedstrijd.contact_naam,
            'org_tel': wedstrijd.contact_telefoon,

            'email_cs': self._email_cs,
        }

        mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_GEKOZEN)

        mailer_queue_email(account.bevestigde_email,
                           'Geselecteerd voor wedstrijd %s' % wed_datum,
                           mail_body)

    def stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig(self, dag, sporter):
        """ Stuur een e-mail om de de-keuze te melden """

        self.stdout.write('[INFO] Stuur e-mail naar SR %s: voor wedstrijd niet meer nodig' % sporter.lid_nr)

        if not sporter.account:
            self.stderr.write('[ERROR] Sporter %s heeft geen account. Mail wordt niet gestuurd.' % sporter.lid_nr)
            return

        account = sporter.account
        wedstrijd = dag.wedstrijd

        datum = wedstrijd.datum_begin + datetime.timedelta(days=dag.dag_offset)
        wed_datum = date_format(datum, "j F Y")

        context = {
            'voornaam': account.get_first_name(),

            'wed_titel': wedstrijd.titel,
            'wed_datum': wed_datum,

            'email_cs': self._email_cs,
        }

        mail_body = render_email_template(context, EMAIL_TEMPLATE_VOOR_WEDSTRIJDDAG_NIET_MEER_NODIG)

        mailer_queue_email(account.bevestigde_email,
                           'Niet meer nodig voor wedstrijd %s' % wed_datum,
                           mail_body)

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

    def _verwerk_mutatie_beschikbaarheid_opvragen(self, mutatie):
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
                self.stuur_email_naar_sr_beschikbaarheid_opgeven(wedstrijd, vraag, sporter.account)
        # for

    def _verwerk_mutatie_stuur_notificaties(self, mutatie):
        wedstrijd = mutatie.wedstrijd

        when_str = timezone.localtime(mutatie.when).strftime('%Y-%m-%d om %H:%M')

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
                        self.stuur_email_naar_sr_voor_wedstrijddag_gekozen(dag, sporter)
                        dag.notified_srs.add(sporter)
            # for

            # alle overgebleven srs zijn niet meer gekozen en kunnen dus een afmelding krijgen
            for sporter in Sporter.objects.filter(pk__in=notified_pks):
                self.stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig(dag, sporter)
                dag.notified_srs.remove(sporter)
            # for
        # for

        # stuur de mailtjes (voor alle dagen in 1x)

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.mutatie

        if code == SCHEIDS_MUTATIE_BESCHIKBAARHEID_OPVRAGEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Beschikbaarheid opvragen' % mutatie.pk)
            self._verwerk_mutatie_beschikbaarheid_opvragen(mutatie)

        elif code == SCHEIDS_MUTATIE_STUUR_NOTIFICATIES:
            self.stdout.write('[INFO] Verwerk mutatie %s: Scheidsrechters gekozen' % mutatie.pk)
            self._verwerk_mutatie_stuur_notificaties(mutatie)

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

        did_useful_work = False
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
                did_useful_work = True
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

    test uitvoeren met --debug-mode anders wordt er niets bijgehouden
"""

# end of file
