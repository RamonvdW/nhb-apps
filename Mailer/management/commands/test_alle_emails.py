# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" dit commando kan gebruikt worden voor het verifiëren van alle e-mails die de site kan produceren """

from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand
from Account.models import Account
from Account.operations.otp import otp_stuur_email_losgekoppeld
from Account.view_wachtwoord import account_stuur_email_wachtwoord_vergeten
from Account.operations.email import account_stuur_email_bevestig_nieuwe_email
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.management.commands.bestel_mutaties import stuur_email_naar_koper_betaalbevestiging
from Bestelling.definities import BESTELLING_STATUS_NIEUW
from Bestelling.models import Bestelling, BestellingProduct
from Betaal.definities import TRANSACTIE_TYPE_MOLLIE_PAYMENT, TRANSACTIE_TYPE_MOLLIE_RESTITUTIE
from Betaal.models import BetaalInstellingenVereniging, BetaalTransactie
from Competitie.models import Competitie, CompetitieMatch
from Functie.models import Functie
from Functie.view_koppel_beheerder import functie_wijziging_stuur_email_notificatie, functie_vraag_email_bevestiging
from Geo.models import Regio
from Locatie.models import WedstrijdLocatie
from Mailer.models import MailQueue
from Mailer.operations import mailer_email_is_valide
from Scheidsrechter.management.commands.scheids_mutaties import (stuur_email_naar_sr_beschikbaarheid_opgeven,
                                                                 stuur_email_naar_sr_voor_wedstrijddag_gekozen,
                                                                 stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig,
                                                                 stuur_email_naar_sr_voor_match_gekozen,
                                                                 stuur_email_naar_sr_voor_match_niet_meer_nodig)
from Scheidsrechter.models import WedstrijdDagScheidsrechters
from Sporter.models import Sporter, SporterBoog
from Taken.operations import stuur_email_nieuwe_taak, stuur_email_taak_herinnering
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):

    help = "Stuur alle mogelijke e-mails"

    aantal_verwacht = 14

    test_regio_nr = 100
    test_ver_nr = 9999
    test_lid_nr = 99999
    test_bestel_nr = 999999
    test_functie_beschrijving = 'Test functie 9999'
    test_locatie_naam = 'Test locatie 999999'
    test_sessie_beschrijving = 'Test sessie 99999'
    test_wachtwoord = TEST_WACHTWOORD
    test_email = 'testertje@vander.test'

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self.to_email = ''              # krijgen we via de command line
        self.account = None
        self.bestelling = None
        self.functie = None
        self.mailqueue_last = MailQueue.objects.count()
        self._database_opschonen()

    def add_arguments(self, parser):
        parser.add_argument('to_email',
                            help="E-mailadres waar de mails heen moeten")

    def _database_vullen(self):
        functie = Functie(
                        beschrijving=self.test_functie_beschrijving,
                        rol='MO',
                        bevestigde_email='',
                        nieuwe_email=self.to_email,
                        telefoon='')
        functie.save()
        self.functie = functie

        ver = Vereniging(
                    ver_nr=self.test_ver_nr,
                    naam='Test vereniging',
                    adres_regel1='Eerste adresregel',
                    adres_regel2='Tweede adresregel',
                    plaats='Testplaats',
                    regio=Regio.objects.get(regio_nr=self.test_regio_nr),
                    kvk_nummer='KvkNummer123',
                    website='https://test.verenig.ing',
                    contact_email='contact@verenig.ing',
                    telefoonnummer='nr123456',
                    bank_iban='TestIBAN1234',
                    bank_bic='TestBIC1234')
        ver.save()

        boog_r = BoogType.objects.get(afkorting='R')
        boog_c = BoogType.objects.get(afkorting='C')

        sporter1 = Sporter(
                        lid_nr=self.test_lid_nr,
                        voornaam=self.account.first_name,
                        achternaam=self.account.last_name,
                        unaccented_naam=self.account.unaccented_naam,
                        email=self.to_email,
                        geboorte_datum='1970-07-07',
                        geslacht='X',
                        para_classificatie='',
                        sinds_datum='2000-01-01',
                        bij_vereniging=ver,
                        account=self.account)
        sporter1.save()
        self.sporter1 = sporter1

        sporter2 = Sporter(
                        lid_nr=self.test_lid_nr - 1,
                        voornaam=self.account.first_name,
                        achternaam=self.account.last_name,
                        unaccented_naam=self.account.unaccented_naam,
                        email=self.to_email,
                        geboorte_datum='1970-07-07',
                        geslacht='M',
                        para_classificatie='',
                        sinds_datum='2000-01-01',
                        bij_vereniging=ver,
                        account=self.account)
        sporter2.save()

        sporterboog_r = SporterBoog(
                            sporter=sporter1,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog_r.save()

        sporterboog_c = SporterBoog(
                            sporter=sporter2,
                            boogtype=boog_c,
                            voor_wedstrijd=True)
        sporterboog_c.save()

        now = timezone.now()
        wedstrijd_datum = now.date() + timezone.timedelta(days=30)

        locatie = WedstrijdLocatie(
                        naam=self.test_locatie_naam,
                        adres=ver.adres_regel1 + '\n' + ver.adres_regel2,
                        plaats=ver.plaats)
        locatie.save()
        locatie.verenigingen.add(ver)

        sessie = WedstrijdSessie(
                        datum=wedstrijd_datum,
                        tijd_begin='10:00',
                        tijd_einde='15:00',
                        beschrijving=self.test_sessie_beschrijving)
        sessie.save()

        wedstrijd = Wedstrijd(
                        titel='Test wedstrijd 9999',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=wedstrijd_datum,
                        datum_einde=wedstrijd_datum,
                        locatie=locatie,
                        voorwaarden_a_status_when=now,
                        organiserende_vereniging=ver)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        self.wedstrijd = wedstrijd

        wkls_r = KalenderWedstrijdklasse.objects.filter(buiten_gebruik=False, boogtype=boog_r)
        wkls_c = KalenderWedstrijdklasse.objects.filter(buiten_gebruik=False, boogtype=boog_c)

        inschrijving_r = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog_r,
                            koper=self.account,
                            ontvangen_euro=Decimal('42.40'))
        inschrijving_r.save()

        inschrijving_c = WedstrijdInschrijving(
                            wanneer=timezone.now(),
                            status=WEDSTRIJD_INSCHRIJVING_STATUS_BESTELD,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_c[0],
                            sporterboog=sporterboog_c,
                            koper=self.account,
                            ontvangen_euro=Decimal('22.41'))
        inschrijving_c.save()

        product_r = BestellingProduct(
                        wedstrijd_inschrijving=inschrijving_r,
                        prijs_euro=Decimal('42.40'),
                        korting_euro=Decimal('0.00'))
        product_r.save()

        product_c = BestellingProduct(
                        wedstrijd_inschrijving=inschrijving_c,
                        prijs_euro=Decimal('42.41'),
                        korting_euro=Decimal('20.00'))
        product_c.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            mollie_api_key='test_12345')
        instellingen.save()

        bestelling = Bestelling(
                        bestel_nr=self.test_bestel_nr,
                        account=self.account,
                        ontvanger=instellingen,
                        verkoper_naam='Test verkoper naam',
                        verkoper_adres1=ver.adres_regel1,
                        verkoper_adres2=ver.adres_regel2,
                        verkoper_kvk=ver.kvk_nummer,
                        verkoper_email=ver.contact_email,
                        verkoper_telefoon=ver.telefoonnummer,
                        totaal_euro=Decimal("142.42"),
                        status=BESTELLING_STATUS_NIEUW)
        bestelling.save()
        bestelling.producten.add(product_r)
        bestelling.producten.add(product_c)
        self.bestelling = bestelling

        bedrag_euro = Decimal("142.42")
        transactie = BetaalTransactie(
                            when=now - timezone.timedelta(hours=1),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_PAYMENT,
                            payment_id='test_pay_1',
                            beschrijving='Bestelling %s' % self.test_bestel_nr,
                            bedrag_beschikbaar=bedrag_euro,
                            bedrag_te_ontvangen=bedrag_euro,
                            klant_naam='Pietje Schiet',
                            klant_account='RekNr van Pietje')
        transactie.save()
        bestelling.transacties.add(transactie)

        transactie = BetaalTransactie(
                            when=now - timezone.timedelta(minutes=30),
                            transactie_type=TRANSACTIE_TYPE_MOLLIE_RESTITUTIE,
                            payment_id='test_pay_1',
                            beschrijving='Terugbetaling teveel betaald',
                            bedrag_refund=Decimal("5.00"),
                            klant_naam='Pietje Schiet',
                            klant_account='RekNr van Pietje')
        transactie.save()
        bestelling.transacties.add(transactie)

        comp = Competitie(
                    beschrijving='Test competitie',
                    afstand=18,
                    begin_jaar=2000)
        comp.save()

        match = CompetitieMatch(
                        competitie=comp,
                        beschrijving='Test match',
                        datum_wanneer='2000-01-01',
                        tijd_begin_wedstrijd='09:00',
                        aantal_scheids=1)
        match.save()
        match.refresh_from_db()     # provides strings converted to proper structures
        self.match = match

    def _database_opschonen(self):
        try:
            ver = Vereniging.objects.get(ver_nr=self.test_ver_nr)
        except Vereniging.DoesNotExist:      # pragma: no cover
            pass
        else:
            self.bestelling = None
            try:
                bestelling = Bestelling.objects.get(bestel_nr=self.test_bestel_nr)
            except Bestelling.DoesNotExist:      # pragma: no cover
                pass
            else:
                bestelling.producten.all().delete()
                bestelling.delete()

            try:
                instellingen = BetaalInstellingenVereniging.objects.get(vereniging=ver)
            except BetaalInstellingenVereniging.DoesNotExist:      # pragma: no cover
                pass
            else:
                instellingen.delete()

            try:
                sporter1 = Sporter.objects.get(lid_nr=self.test_lid_nr)
                sporter2 = Sporter.objects.get(lid_nr=self.test_lid_nr - 1)
            except Sporter.DoesNotExist:      # pragma: no cover
                pass
            else:
                try:
                    sporterboog1 = SporterBoog.objects.get(sporter=sporter1)
                    sporterboog2 = SporterBoog.objects.get(sporter=sporter2)
                except SporterBoog.DoesNotExist:      # pragma: no cover
                    pass
                else:
                    try:
                        inschrijving1 = WedstrijdInschrijving.objects.get(sporterboog=sporterboog1)
                        inschrijving2 = WedstrijdInschrijving.objects.get(sporterboog=sporterboog2)
                    except WedstrijdInschrijving.DoesNotExist:      # pragma: no cover
                        pass
                    else:
                        inschrijving1.delete()
                        inschrijving2.delete()

                    sporterboog1.delete()
                    sporterboog2.delete()

                sporter1.delete()
                sporter2.delete()

            try:
                wedstrijd = Wedstrijd.objects.get(organiserende_vereniging=ver)
            except Wedstrijd.DoesNotExist:      # pragma: no cover
                pass
            else:
                wedstrijd.delete()

            try:
                locatie = WedstrijdLocatie.objects.get(naam=self.test_locatie_naam)
            except WedstrijdLocatie.DoesNotExist:      # pragma: no cover
                pass
            else:
                locatie.delete()

            ver.delete()

        self.functie = None
        try:
            functie = Functie.objects.get(beschrijving=self.test_functie_beschrijving)
        except Functie.DoesNotExist:      # pragma: no cover
            pass
        else:
            functie.delete()

    def _check_mail_gemaakt(self):
        # controleer dat er 1 mail bijgemaakt is
        mailqueue_count = MailQueue.objects.count()
        if mailqueue_count != self.mailqueue_last + 1:      # pragma: no cover
            self.stderr.write('[ERROR] Geen nieuwe mail kunnen vinden in de MailQueue')
        self.mailqueue_last = mailqueue_count

    def _test_account(self):
        self.stdout.write('Maak mail voor Account - Wachtwoord vergeten')
        account_stuur_email_wachtwoord_vergeten(self.account, email=self.account.bevestigde_email, test=1)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor Account - Bevestig toegang e-mail')
        account_stuur_email_bevestig_nieuwe_email(self.to_email, 'dummy-url')
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor Account - OTP losgekoppeld')
        otp_stuur_email_losgekoppeld(self.account)
        self._check_mail_gemaakt()

    def _test_bestel(self):
        # TODO: Bevestiging bestelling

        self.stdout.write('Maak mail voor Bestel - Betaal bevestiging')
        stuur_email_naar_koper_betaalbevestiging(self.bestelling)
        self._check_mail_gemaakt()

        # TODO: mail naar backoffice

    def _test_functie(self):
        self.stdout.write('Maak mail voor Functie - Bevestig toegang e-mail')
        functie_vraag_email_bevestiging(self.functie)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor Functie - Gewijzigde beheerder (toegevoegd)')
        functie_wijziging_stuur_email_notificatie(self.account, 'not used', 'Test functie', add=True)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor Functie - Gewijzigde beheerder (verwijderd)')
        functie_wijziging_stuur_email_notificatie(self.account, 'not used', 'Test functie', remove=True)
        self._check_mail_gemaakt()

    def _test_registreer(self):
        # TODO: lid-bevestig-toegang-email
        pass

    def _test_registreer_gast(self):
        # TODO: gast-afgewezen
        # TODO: gast-bevestig-toegang-email
        # TODO: gast-tijdelijk-bondsnummer
        # TODO: gast-verwijder
        pass

    def _test_scheids(self):
        email_cs = 'scheids@mh.not'
        datum = datetime(2000, 1, 1)

        self.stdout.write('Maak mail voor SR - Beschikbaarheid opgeven')
        stuur_email_naar_sr_beschikbaarheid_opgeven(self.wedstrijd, [datum], self.account, email_cs)
        self._check_mail_gemaakt()

        dag = WedstrijdDagScheidsrechters(wedstrijd=self.wedstrijd)
        dag.save()

        self.stdout.write('Maak mail voor SR - Gekozen voor wedstrijd')
        stuur_email_naar_sr_voor_wedstrijddag_gekozen(dag, self.sporter1, email_cs)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor SR - Niet meer nodig voor wedstrijd')
        stuur_email_naar_sr_voor_wedstrijddag_niet_meer_nodig(dag, self.sporter1, email_cs)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor SR - Gekozen voor match')
        stuur_email_naar_sr_voor_match_gekozen(self.match, self.sporter1, email_cs)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor SR - Niet meer nodig voor match')
        stuur_email_naar_sr_voor_match_niet_meer_nodig(self.match, self.sporter1, email_cs)
        self._check_mail_gemaakt()

    def _test_taken(self):
        self.stdout.write('Maak mail voor Taken - Nieuwe taak')
        stuur_email_nieuwe_taak(self.to_email, 'Nieuwe taak', 42)
        self._check_mail_gemaakt()

        self.stdout.write('Maak mail voor Taken - Herinnering')
        stuur_email_taak_herinnering(self.to_email, 42)
        self._check_mail_gemaakt()

    def _check_to_email(self):
        if not mailer_email_is_valide(self.to_email):
            self.stderr.write('Geen valide e-mailadres')
            return False

        if len(settings.EMAIL_ADDRESS_WHITELIST) > 0:
            if self.to_email not in settings.EMAIL_ADDRESS_WHITELIST:
                self.stdout.write('[WARNING] E-mailadres is niet white-listed!')

        try:
            self.account = (Account
                            .objects
                            .get(bevestigde_email=self.to_email))
        except Account.DoesNotExist:
            self.stderr.write('Geen account gevonden met dit e-mailadres')
            return False

        return True

    def handle(self, *args, **options):
        self.to_email = options['to_email']

        mailqueue_pre = self.mailqueue_last

        if self._check_to_email():
            # nu is self.account_email ingevuld en gecontroleerd
            self._database_vullen()

            # test iedereen die Mailer.operations.mailer_queue_email gebruikt
            self._test_account()
            self._test_bestel()
            self._test_functie()
            self._test_registreer()
            self._test_registreer_gast()
            self._test_scheids()
            self._test_taken()
            # fout 500 e-mail wordt niet getest

        self._database_opschonen()

        mailqueue_post = MailQueue.objects.count()
        aantal = mailqueue_post - mailqueue_pre
        if aantal != self.aantal_verwacht:
            self.stderr.write('[ERROR] Er zijn %s mails aangemaakt in plaats van %s' % (aantal, self.aantal_verwacht))
        else:
            self.stdout.write('Succes: er zijn %s e-mails aangemaakt, zoals verwacht' % aantal)


# end of file
