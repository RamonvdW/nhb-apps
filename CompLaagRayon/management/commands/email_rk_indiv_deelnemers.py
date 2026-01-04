# -*- coding: utf-8 -*-
import functools

#  Copyright (c) 2025-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django.core.management.base import BaseCommand
from Competitie.definities import DEEL_RK, DEELNAME_ONBEKEND
from Competitie.models import Competitie, Kampioenschap, CompetitieMatch, KampioenschapSporterBoog
from Functie.models import Functie
from Mailer.operations import mailer_queue_email, render_email_template
from Vereniging.models import Vereniging

EMAIL_TEMPLATE_BEVESTIG_DEELNAME = 'email_complaagrayon/bevestig-deelname.dtl'


class Command(BaseCommand):

    help = "E-mail RK individueel deelnemers met status=onbekend"

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.competitie = None
        self.deelkamp = None
        self.rk_kort = ''
        self.matches = dict()               # [indiv_klasse.pk] = (CompetitieMatch, CompetitieIndivKlasse)
        self.error_msgs = list()
        self.deelname_onbekend = list()     # [(deelnemer, match), ..]
        self.email_count = 0
        self.now = timezone.now()

    def add_arguments(self, parser):
        parser.add_argument('afstand', type=str, choices=('18', '25'), help='Competitie afstand (18/25)')
        parser.add_argument('rayon', type=int, choices=(1, 2, 3, 4))
        parser.add_argument('--stuur', action='store_true', help='Stuur de e-mail')

    def _zoek_kampioenschap(self, afstand, rayon):
        for comp in Competitie.objects.filter(afstand=afstand):
            comp.bepaal_fase()
            if comp.fase_indiv < 'E':
                # skip nieuwe competitie in regio fase
                continue

            self.competitie = comp
        # for
        if not self.competitie:
            return
        # self.stdout.write('[INFO] Competitie: %s' % self.competitie)

        # "RK Indoor rayon 3"
        # "RK 25m 1pijl rayon 2"
        if self.competitie.afstand == "18":
            self.rk_kort = 'RK Indoor'
        else:
            self.rk_kort = 'RK 25m 1pijl'

        self.deelkamp = (Kampioenschap
                         .objects
                         .filter(competitie=self.competitie,
                                 deel=DEEL_RK,
                                 rayon__rayon_nr=rayon)
                         .select_related('rayon',
                                         'competitie')
                         .prefetch_related('rk_bk_matches')
                         .first())
        if self.deelkamp:
            self.stdout.write('[INFO] Kampioenschap: %s' % self.deelkamp)
            self.rk_kort += ' rayon %s' % self.deelkamp.rayon.rayon_nr

    @functools.cache
    def _get_email_hwl(self, ver_nr: Vereniging) -> str:
        functie = Functie.objects.filter(rol='HWL', vereniging__ver_nr=ver_nr).first()
        if functie:
            return functie.bevestigde_email
        return ''

    def _zoek_matches(self):
        # verzamel de match voor elke klasse
        for match in (self.deelkamp
                      .rk_bk_matches
                      .exclude(vereniging=None)
                      .select_related('vereniging',
                                      'locatie')
                      .prefetch_related('indiv_klassen')):

            # laat contact opnemen met de HWL ipv de SEC
            email = self._get_email_hwl(match.vereniging.ver_nr)
            if email:
                match.vereniging.contact_email = email

            for klasse in match.indiv_klassen.all():
                self.matches[klasse.pk] = (match, klasse)
            # for
        # for
        self.stdout.write('[INFO] %s RK wedstrijden gevonden' % len(self.matches))

    def _zoek_deelnemers(self):
        seizoen_url = self.competitie.maak_seizoen_url()
        rayon_nr = self.deelkamp.rayon.rayon_nr

        # doorloop de sporters
        self.error_msgs = list()
        for deelnemer in (KampioenschapSporterBoog
                          .objects
                          .filter(kampioenschap=self.deelkamp,
                                  deelname=DEELNAME_ONBEKEND)
                          .exclude(sporterboog__sporter__bij_vereniging=None)
                          .select_related('kampioenschap__rayon',
                                          'sporterboog__sporter',
                                          'sporterboog__sporter__account',
                                          'indiv_klasse')):

            comp_boog = deelnemer.sporterboog.boogtype.afkorting.lower()
            deelnemer.url_deelnemerslijst = settings.SITE_URL + reverse('CompUitslagen:uitslagen-rk-indiv-n',
                                                                        kwargs={'comp_pk_of_seizoen': seizoen_url,
                                                                                'rayon_nr': rayon_nr,
                                                                                'comp_boog': comp_boog})

            try:
                match, klasse = self.matches[deelnemer.indiv_klasse.pk]
            except KeyError:
                msg = 'Geen wedstrijd voor klasse %s' % deelnemer.indiv_klasse
                if msg not in self.error_msgs:
                    self.error_msgs.append(msg)

                tup = (deelnemer, None)
            else:
                tup = (deelnemer, match)

            self.deelname_onbekend.append(tup)
        # for

    def _stuur_email(self, deelnemer: KampioenschapSporterBoog, match: CompetitieMatch, url_deelnemerslijst):
        """ Stuur een e-mail """

        sporter = deelnemer.sporterboog.sporter
        account = sporter.account
        if not account:
            return

        org_ver = match.vereniging
        if match.locatie:
            adres = match.locatie.adres_oneliner()
        else:
            adres = 'nog onbekend (volgt later)'

        context = {
            'naam_site': settings.NAAM_SITE,
            'voornaam': account.get_first_name(),
            'rk_kort': self.rk_kort,
            'klasse': deelnemer.indiv_klasse,
            'match': match,
            'locatie_adres': adres,
            'sporterboog': deelnemer.sporterboog,
            'contact_tel': org_ver.telefoonnummer,
            'contact_email': org_ver.contact_email,
            'url_deelnemerslijst': url_deelnemerslijst,
        }

        mail_body = render_email_template(context, EMAIL_TEMPLATE_BEVESTIG_DEELNAME)

        mailer_queue_email(account.bevestigde_email,
                           'Kan je deelnemen aan het ' + self.rk_kort + '?',
                           mail_body)

        deelnemer.bevestiging_gevraagd_op = self.now
        deelnemer.save(update_fields=['bevestiging_gevraagd_op'])

        self.email_count += 1

    def handle(self, *args, **options):

        afstand = options['afstand']
        rayon_nr = options['rayon']
        do_stuur = options['stuur']

        self._zoek_kampioenschap(afstand, rayon_nr)
        if not self.competitie or not self.deelkamp:
            self.stdout.write('[ERROR] Competitie niet gevonden')
            return

        self._zoek_matches()

        self._zoek_deelnemers()
        if len(self.error_msgs):
            self.stdout.write('[ERROR] %s fouten gevonden' % len(self.error_msgs))
            self.error_msgs.sort()
            for msg in self.error_msgs:
                self.stdout.write('  %s' % msg)
            # for
            return

        self.stdout.write('[INFO] Deelname onbekend: %s sporters' % len(self.deelname_onbekend))

        if do_stuur:
            for deelnemer, match in self.deelname_onbekend:
                self._stuur_email(deelnemer, match, deelnemer.url_deelnemerslijst)
            # for
            self.stdout.write('[INFO] %s e-mails verstuurd' % self.email_count)


# end of file
