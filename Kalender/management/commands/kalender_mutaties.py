# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" achtergrondtaak om mutaties te verwerken zodat concurrency voorkomen kan worden
    deze komen binnen via KalenderMutatie
"""

from django.conf import settings
from django.utils import timezone
from django.db.models import F
from django.core.management.base import BaseCommand
from Kalender.models import (KalenderMutatie, KALENDER_MUTATIE_INSCHRIJVEN, KALENDER_MUTATIE_AFMELDEN,
                             KALENDER_MUTATIE_KORTING)
from Mandje.models import MandjeInhoud
from Overig.background_sync import BackgroundSync
from Taken.taken import maak_taak
import django.db.utils
import traceback
import datetime
import sys

VOLGORDE_PARKEER = 22222        # hoog en past in PositiveSmallIntegerField


class Command(BaseCommand):
    help = "Kalender mutaties verwerken"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)

        self.stop_at = datetime.datetime.now()

        self._sync = BackgroundSync(settings.BACKGROUND_SYNC__KALENDER_MUTATIES)
        self._count_ping = 0

        self._hoogste_mutatie_pk = None

    def add_arguments(self, parser):
        parser.add_argument('duration', type=int,
                            choices={1, 2, 5, 7, 10, 15, 20, 30, 45, 60},
                            help="Aantal minuten actief blijven")
        parser.add_argument('--quick', action='store_true')     # for testing

    def _verwerk_mutatie_inschrijven(self, mutatie):
        # voeg deze inschrijving toe aan het mandje van de koper
        inschrijving = mutatie.inschrijving
        if inschrijving is None:
            self.stderr.write('[WARNING] Inschrijf mutatie heeft geen inschrijving (meer) - skipping')
            return

        sessie = inschrijving.sessie

        if True or sessie.prijs_euro > 0.0:
            # leg deze bestelling in het mandje zodat er afgerekend kan worden
            MandjeInhoud(
                    account=inschrijving.koper,
                    inschrijving=inschrijving,
                    prijs_euro=sessie.prijs_euro).save()
        # else:
        #     # gratis deelname loopt niet via het mandje
        #     inschrijving.betaling_voldaan = True
        #     inschrijving.save(update_fields=['betaling_voldaan'])

        # verhoog het aantal inschrijvingen op deze sessie
        sessie.aantal_inschrijvingen += 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

    def _verwerk_mutatie_afmelden(self, mutatie):

        # verwijder de inschrijving bij de wedstrijd
        inschrijving = mutatie.inschrijving
        if inschrijving is None:
            self.stderr.write('[WARNING] Afmeld mutatie heeft geen inschrijving (meer) - skipping')
            return

        sessie = inschrijving.sessie

        # verwijder deze inschrijving uit het mandje
        try:
            inhoud = (MandjeInhoud
                      .objects
                      .select_related('account')
                      .get(account=inschrijving.koper,
                           inschrijving=inschrijving))

        except MandjeInhoud.DoesNotExist:
            # vaag, maar niets aan te doen --> klaag in de log
            self.stderr.write('[ERROR] Kan inschrijving pk=%s van koper pk=%s niet in een mandje vinden' % (
                                inschrijving.pk, inschrijving.koper.pk))
        else:
            if inschrijving.betaling_voldaan:
                # TODO: restitutie opzetten
                self.stderr.write('[ERROR] Kan restitutie nog niet doen')

            self.stdout.write('[INFO] Inhoud pk=%s verwijderd uit het mandje van account %s' % (
                                inhoud.pk, inhoud.account.pk))
            inhoud.delete()

        # schrijf de sporter uit bij de sessie
        sessie.aantal_inschrijvingen -= 1
        sessie.save(update_fields=['aantal_inschrijvingen'])

        mutatie.inschrijving = None
        mutatie.save(update_fields=['inschrijving'])

        self.stdout.write('[INFO] Verwijder inschrijving pk=%s' % inschrijving.pk)
        inschrijving.delete()

    def _verwerk_mutatie_korting(self, mutatie):
        """ Deze functie controleert of een kortingscode toegepast mag worden op de inschrijvingen
            die in het mandje van het account staan.
        """
        korting = mutatie.korting
        account = mutatie.korting_voor_account

        # controleer de geldigheidsdatum
        if korting.geldig_tot_en_met < timezone.now().date():
            self.stdout.write('[WARNING] Kortingscode pk=%s is niet meer geldig' % korting.pk)
            return

        # zoek regels in het mandje en kijk of de code toegepast kan worden
        for inhoud in (MandjeInhoud
                       .objects
                       .exclude(inschrijving=None)      # alleen kalender inschrijvingen vinden
                       .filter(account=account)
                       .select_related('inschrijving')):

            toepassen = False

            if korting.voor_sporter:
                self.stdout.write('[DEBUG] Korting: voor_sporter=%s' % korting.voor_sporter)
                # code voor een specifiek sporter
                if korting.voor_sporter == inhoud.inschrijving.sporterboog.sporter:
                    toepassen = True
                    self.stdout.write('[DEBUG] Korting: juiste voor_sporter')

            if korting.voor_vereniging:
                self.stdout.write('[DEBUG] Korting: voor_vereniging=%s' % korting.voor_vereniging)
                # alle sporters van deze vereniging mogen deze code gebruiken
                # (bijvoorbeeld de organiserende vereniging)
                if korting.voor_sporter.bij_vereniging == inhoud.inschrijving.sporterboog.sporter.bij_vereniging:
                    toepassen = True
                    self.stdout.write('[DEBUG] Korting: juiste voor_vereniging')

            if korting.voor_wedstrijd.all().count() > 0:
                # korting is begrensd tot 1 wedstrijd of een serie wedstrijden
                if korting.voor_wedstrijd.filter(id=inhoud.inschrijving.wedstrijd.id).exists():
                    # code voor een specifieke wedstrijd
                    toepassen = True
                    self.stdout.write('[DEBUG] Korting: juiste wedstrijd %s' % inhoud.inschrijving.wedstrijd)
                else:
                    # leuke code, maar niet bedoeld voor deze wedstrijd
                    toepassen = False
                    self.stdout.write('[DEBUG] Korting: verkeerde wedstrijd')

            if toepassen:
                # TODO: bij gebruik meerdere codes alleen de hoogste korting geven
                self.stdout.write('[INFO] Korting pk=%s toepassen op mandje inhoud pk=%s' % (korting.pk, inhoud.pk))
            else:
                # self.stdout.write('[INFO] Korting pk=%s niet toepassen' % korting.pk)
                pass

        # for

    def _verwerk_mutatie(self, mutatie):
        code = mutatie.code

        if code == KALENDER_MUTATIE_INSCHRIJVEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Inschrijven' % mutatie.pk)
            self._verwerk_mutatie_inschrijven(mutatie)

        elif code == KALENDER_MUTATIE_AFMELDEN:
            self.stdout.write('[INFO] Verwerk mutatie %s: Afmelden' % mutatie.pk)
            self._verwerk_mutatie_afmelden(mutatie)

        elif code == KALENDER_MUTATIE_KORTING:
            self.stdout.write('[INFO] Verwerk mutatie %s: Korting' % mutatie.pk)
            self._verwerk_mutatie_korting(mutatie)

        else:
            self.stdout.write('[ERROR] Onbekende mutatie code %s (pk=%s)' % (code, mutatie.pk))

    def _verwerk_nieuwe_mutaties(self):
        begin = datetime.datetime.now()

        mutatie_latest = KalenderMutatie.objects.latest('pk')
        # als hierna een extra mutatie aangemaakt wordt dan verwerken we een record
        # misschien dubbel, maar daar kunnen we tegen

        if self._hoogste_mutatie_pk:
            # gebruik deze informatie om te filteren
            self.stdout.write('[INFO] vorige hoogste KalenderMutatie pk is %s' % self._hoogste_mutatie_pk)
            qset = (KalenderMutatie
                    .objects
                    .select_related('inschrijving',
                                    'inschrijving__sporterboog__sporter'
                                    'korting',
                                    'korting__voor_sporter',
                                    'korting__voor_vereniging',
                                    'korting__voor_wedstrijd')
                    .filter(pk__gt=self._hoogste_mutatie_pk))
        else:
            qset = (KalenderMutatie
                    .objects
                    .select_related('inschrijving',
                                    'korting')
                    .all())

        mutatie_pks = qset.values_list('pk', flat=True)

        self._hoogste_mutatie_pk = mutatie_latest.pk

        did_useful_work = False
        for pk in mutatie_pks:
            # LET OP: we halen de records hier 1 voor 1 op
            #         zodat we verse informatie hebben inclusief de vorige mutatie
            mutatie = (KalenderMutatie
                       .objects
                       .select_related('inschrijving',
                                       'inschrijving__wedstrijd',
                                       'inschrijving__sessie',
                                       'inschrijving__sporterboog',
                                       'inschrijving__sporterboog__sporter',
                                       'inschrijving__koper')
                       .get(pk=pk))
            if not mutatie.is_verwerkt:
                self._verwerk_mutatie(mutatie)
                mutatie.is_verwerkt = True
                mutatie.save(update_fields=['is_verwerkt'])
                did_useful_work = True
        # for

        if did_useful_work:
            self.stdout.write('[INFO] nieuwe hoogste KalenderMutatie pk is %s' % self._hoogste_mutatie_pk)

            klaar = datetime.datetime.now()
            self.stdout.write('[INFO] Mutaties verwerkt in %s seconden' % (klaar - begin))

    def _monitor_nieuwe_mutaties(self):
        # monitor voor nieuwe mutaties
        mutatie_count = 0      # moet 0 zijn: beschermd tegen query op lege mutatie tabel
        now = datetime.datetime.now()
        while now < self.stop_at:                   # pragma: no branch
            # self.stdout.write('tick')
            new_count = KalenderMutatie.objects.count()
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
        # trek er nog eens 15 seconden vanaf, om overlap van twee cron jobs te voorkomen
        duration = options['duration']

        self.stop_at = (datetime.datetime.now()
                        + datetime.timedelta(minutes=duration)
                        - datetime.timedelta(seconds=15))

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
        except django.db.utils.DataError as exc:        # pragma: no cover
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
