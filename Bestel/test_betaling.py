# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType
from Bestel.models import BestelMandje, Bestelling, BESTELLING_STATUS_AFGEROND
from Bestel.mutaties import bestel_mutatieverzoek_inschrijven_wedstrijd, bestel_mutatieverzoek_betaling_afgerond
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalMutatie, BetaalTransactie
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Kalender.models import (KalenderWedstrijd, KalenderWedstrijdSessie, WEDSTRIJD_STATUS_GEACCEPTEERD,
                             KalenderInschrijving, INSCHRIJVING_STATUS_DEFINITIEF)
from NhbStructuur.models import NhbRegio, NhbVereniging
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Wedstrijden.models import WedstrijdLocatie
from decimal import Decimal
import re


class TestBestelBetaling(E2EHelpers, TestCase):

    """ tests voor de Bestel applicatie, samenwerking met Betaal applicatie """

    test_after = ('Bestel.test_bestelling',)

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_bestelling_afrekenen = '/bestel/afrekenen/%s/'      # bestel_nr

    url_websim_api = 'http://localhost:8125'
    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver_nhb = NhbVereniging(
                    ver_nr=settings.BETAAL_VIA_NHB_VER_NR,
                    naam='Bondsbureau',
                    plaats='Schietstad',
                    regio=NhbRegio.objects.get(regio_nr=100))
        ver_nhb.save()
        self.ver_nhb = ver_nhb

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_nhb,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_nhb = instellingen

        ver = NhbVereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=NhbRegio.objects.get(regio_nr=112))
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_nhb=True)
        instellingen.save()
        self.instellingen = instellingen

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Ad',
                        achternaam='de Admin',
                        geboorte_datum='1966-06-06',
                        sinds_datum='2020-02-02',
                        account=account,
                        bij_vereniging=ver)
        sporter.save()
        self.sporter = sporter

        boog_r = BoogType.objects.get(afkorting='R')

        sporterboog = SporterBoog(
                            sporter=sporter,
                            boogtype=boog_r,
                            voor_wedstrijd=True)
        sporterboog.save()

        now = timezone.now()
        datum = now.date()      # pas op met testen ronde 23:59

        locatie = WedstrijdLocatie(
                        naam='Test locatie',
                        discipline_outdoor=True,
                        buiten_banen=10,
                        buiten_max_afstand=90,
                        adres='Schietweg 1, Boogdorp',
                        plaats='Boogdrop')
        locatie.save()
        locatie.verenigingen.add(ver)

        sessie = KalenderWedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    prijs_euro=10.00,
                    max_sporters=50)
        sessie.save()
        self.sessie = sessie
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = KalenderWedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        voorwaarden_a_status_when=now)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()

        inschrijving = KalenderInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            sporterboog=sporterboog,
                            koper=account)
        inschrijving.save()
        self.inschrijving = inschrijving

        mandje, is_created = BestelMandje.objects.get_or_create(account=account)
        self.mandje = mandje

    def test_afrekenen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname met kortingscode
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.all()[0]

        # betaling opstarten
        url_betaling_gedaan = '/plein/'     # TODO: betere url kiezen
        description = 'Test betaling 421'       # 421 = paid, iDEAL
        betaal_mutatieverzoek_start_ontvangst(bestelling, description, self.sessie.prijs_euro, url_betaling_gedaan, snel=True)
        f1, f2 = self.verwerk_betaal_mutaties(self.url_websim_api)
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())

        # check dat de transactie inderdaad opgestart is
        bestelling = Bestelling.objects.select_related('betaal_mutatie', 'betaal_actief').get(pk=bestelling.pk)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNotNone(bestelling.betaal_actief)      # BetaalActief
        self.assertEqual(0, bestelling.transacties.count())

        betaal_mutatie = bestelling.betaal_mutatie
        self.assertTrue(betaal_mutatie.url_checkout != '')
        self.assertTrue(betaal_mutatie.payment_id != '')

        betaal_actief = bestelling.betaal_actief
        self.assertEqual(betaal_actief.ontvanger, self.instellingen_nhb)    # want akkoord_via_nhb
        self.assertTrue(betaal_actief.payment_id != '')
        self.assertEqual(betaal_actief.payment_status, 'open')

        # fake het gebruik van de CPSP checkout en de payment-status-changed callback
        count = BetaalMutatie.objects.count()
        resp = self.client.post(self.url_betaal_webhook, {'id': betaal_mutatie.payment_id})
        # self.e2e_dump_resp(resp)
        self.assertEqual(resp.status_code, 200)     # 200 = success, 400 = error
        self.assertEqual(BetaalMutatie.objects.count(), count+1)

        # laat de mutatie verwerken die door de callback aangemaakt is
        count = BetaalTransactie.objects.count()
        f1, f2 = self.verwerk_betaal_mutaties(self.url_websim_api)
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        self.assertTrue('status aangepast: open --> paid' in f2.getvalue())

        betaal_actief = BetaalActief.objects.get(pk=bestelling.betaal_actief.pk)
        self.assertEqual(betaal_actief.payment_status, 'paid')

        # betaal mutatie heeft BetaalTransactie aangemaakt
        self.assertEqual(BetaalTransactie.objects.count(), count+1)

        # koppeling van transactie aan bestelling wordt door bestel daemon gedaan
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(0, bestelling.transacties.count())

        # laat mutatie verwerken die betaal daemon richting bestel daemon heeft gestuurd
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1:', f1.getvalue(), '\nf2:', f2.getvalue())
        msg = f2.getvalue()
        msg = re.sub('pk=[0-9]*', 'pk=X', msg)
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling 1000001 (pk=X)' in msg)
        self.assertTrue('[INFO] Bestelling 1000001 (pk=X) heeft 10.00 van de 10.00 euro ontvangen' in msg)
        self.assertTrue('[INFO] Bestelling 1000001 (pk=X) is afgerond' in msg)

        self.assertEqual(1, bestelling.transacties.count())

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNone(bestelling.betaal_actief)         # BetaalActief
        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat de inschrijving nu op 'definitief' staat
        inschrijving = KalenderInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('10'))
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

# end of file