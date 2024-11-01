# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from BasisTypen.models import BoogType, KalenderWedstrijdklasse
from Bestelling.definities import BESTELLING_STATUS_AFGEROND
from Bestelling.models import BestellingMandje, Bestelling
from Bestelling.operations.mutaties import bestel_mutatieverzoek_inschrijven_wedstrijd
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalMutatie, BetaalTransactie
from Betaal.mutaties import betaal_mutatieverzoek_start_ontvangst
from Geo.models import Regio
from Mailer.models import MailQueue
from Locatie.models import WedstrijdLocatie
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF
from Wedstrijden.models import Wedstrijd, WedstrijdSessie, WedstrijdInschrijving
from decimal import Decimal
import re


class TestBestellingBetaling(E2EHelpers, TestCase):

    """ tests voor de applicatie Bestelling, samenwerking met applicatie Betaal """

    test_after = ('Bestelling.tests.test_bestelling',)

    url_mandje_bestellen = '/bestel/mandje/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_afrekenen = '/bestel/afrekenen/%s/'                 # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr

    url_betaal_webhook = '/bestel/betaal/webhooks/mollie/'

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver,
                            akkoord_via_bond=True)
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

        sessie = WedstrijdSessie(
                    datum=datum,
                    tijd_begin='10:00',
                    tijd_einde='11:00',
                    max_sporters=50)
        sessie.save()
        self.sessie = sessie
        # sessie.wedstrijdklassen.add()

        # maak een kalenderwedstrijd aan, met sessie
        wedstrijd = Wedstrijd(
                        titel='Test',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        locatie=locatie,
                        organiserende_vereniging=ver,
                        voorwaarden_a_status_when=now,
                        prijs_euro_normaal=10.00,
                        prijs_euro_onder18=10.00)
        wedstrijd.save()
        wedstrijd.sessies.add(sessie)
        # wedstrijd.boogtypen.add()
        self.wedstrijd = wedstrijd

        wkls_r = KalenderWedstrijdklasse.objects.filter(boogtype=boog_r, buiten_gebruik=False)

        inschrijving = WedstrijdInschrijving(
                            wanneer=now,
                            wedstrijd=wedstrijd,
                            sessie=sessie,
                            wedstrijdklasse=wkls_r[0],
                            sporterboog=sporterboog,
                            koper=account)
        inschrijving.save()
        self.inschrijving = inschrijving

        mandje, is_created = BestellingMandje.objects.get_or_create(account=account)
        self.mandje = mandje

    def test_afrekenen(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_check_rol('sporter')

        # bestel wedstrijddeelname met korting
        bestel_mutatieverzoek_inschrijven_wedstrijd(self.account_admin, self.inschrijving, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        # betaling opstarten
        url_betaling_gedaan = '/plein/'     # FUTURE: betere url kiezen
        description = 'Test betaling 421'       # 421 = paid, iDEAL
        betaal_mutatieverzoek_start_ontvangst(bestelling, description, self.wedstrijd.prijs_euro_normaal,
                                              url_betaling_gedaan, snel=True)
        self.verwerk_betaal_mutaties()

        # check dat de transactie inderdaad opgestart is
        bestelling = Bestelling.objects.select_related('betaal_mutatie', 'betaal_actief').get(pk=bestelling.pk)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNotNone(bestelling.betaal_actief)      # BetaalActief
        self.assertEqual(0, bestelling.transacties.count())

        betaal_mutatie = bestelling.betaal_mutatie
        self.assertTrue(betaal_mutatie.url_checkout != '')
        self.assertTrue(betaal_mutatie.payment_id != '')

        betaal_actief = bestelling.betaal_actief
        self.assertEqual(betaal_actief.ontvanger, self.instellingen_bond)    # want akkoord_via_bond
        self.assertTrue(betaal_actief.payment_id != '')
        self.assertEqual(betaal_actief.payment_status, 'open')

        # haal de betaal status pagina op
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_na_de_betaling % bestelling.bestel_nr, {'snel': 1})
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/bestelling-afgerond.dtl', 'plein/site_layout.dtl'))

        # fake het gebruik van de CPSP checkout en de payment-status-changed callback
        count = BetaalMutatie.objects.count()
        resp = self.client.post(self.url_betaal_webhook, {'id': betaal_mutatie.payment_id})
        # self.e2e_dump_resp(resp)
        self.assertEqual(resp.status_code, 200)     # 200 = success, 400 = error
        self.assertEqual(BetaalMutatie.objects.count(), count+1)

        # laat de mutatie verwerken die door de callback aangemaakt is
        count = BetaalTransactie.objects.count()
        f1, f2 = self.verwerk_betaal_mutaties()
        self.assertTrue("status aangepast: 'open' --> 'paid'" in f2.getvalue())

        betaal_actief = BetaalActief.objects.get(pk=bestelling.betaal_actief.pk)
        self.assertEqual(betaal_actief.payment_status, 'paid')

        # betaal mutatie heeft BetaalTransactie aangemaakt
        self.assertEqual(BetaalTransactie.objects.count(), count+1)

        # koppeling van transactie aan bestelling wordt door bestel daemon gedaan
        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(0, bestelling.transacties.count())

        # maak de uitgaande mail queue leeg
        MailQueue.objects.all().delete()

        # laat mutatie verwerken die betaal daemon richting bestel daemon heeft gestuurd
        f1, f2 = self.verwerk_bestel_mutaties()
        msg = f2.getvalue()
        msg = re.sub(r'pk=[0-9]+', 'pk=X', msg)
        self.assertTrue('[INFO] Betaling is gelukt voor bestelling MH-1002001 (pk=X)' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) heeft € 10,00 van de € 10,00 ontvangen' in msg)
        self.assertTrue('[INFO] Bestelling MH-1002001 (pk=X) is afgerond' in msg)

        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat een e-mailbevestiging van de betaling aangemaakt is
        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-betaling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Prijs:', '>Korting:'))

        bestelling = Bestelling.objects.get(pk=bestelling.pk)
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertIsNotNone(bestelling.betaal_mutatie)     # BetaalMutatie
        self.assertIsNone(bestelling.betaal_actief)         # BetaalActief
        self.assertEqual(1, bestelling.transacties.count())

        # controleer dat de inschrijving nu op 'definitief' staat
        inschrijving = WedstrijdInschrijving.objects.get(pk=self.inschrijving.pk)
        self.assertEqual(inschrijving.status, WEDSTRIJD_INSCHRIJVING_STATUS_DEFINITIEF)
        self.assertEqual(inschrijving.ontvangen_euro, Decimal('10'))
        self.assertEqual(inschrijving.retour_euro, Decimal('0'))

        # bij nog een poging om te betalen worden we doorgestuurd
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_afrekenen % bestelling.bestel_nr)
        self.assert_is_redirect(resp, self.url_na_de_betaling % bestelling.bestel_nr)

# end of file
