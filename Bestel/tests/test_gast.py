# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestel.definities import (BESTELLING_STATUS_AFGEROND, BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_NIEUW,
                               BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD)
from Bestel.models import BestelMandje, BestelMutatie, Bestelling
from Bestel.operations.mutaties import (bestel_mutatieverzoek_webwinkel_keuze,
                                        bestel_mutatieverzoek_betaling_afgerond,
                                        bestel_mutatieverzoek_afmelden_wedstrijd)
from Betaal.models import BetaalInstellingenVereniging, BetaalActief, BetaalTransactie, BetaalMutatie
from Functie.models import Functie
from Mailer.models import MailQueue
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.definities import VERZENDKOSTEN_BRIEFPOST
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal


class TestBestelGast(E2EHelpers, TestCase):

    """ tests voor de Bestel-applicatie, module bestellingen door gast account """

    test_after = ('Bestel.tests.test_mandje', 'Bestel.tests.test_bestelling', 'Registreer.test_gast')

    url_mandje_bestellen = '/bestel/mandje/'
    url_afleveradres = '/bestel/mandje/afleveradres/'
    url_bestellingen_overzicht = '/bestel/overzicht/'
    url_bestelling_details = '/bestel/details/%s/'          # bestel_nr
    url_bestelling_afrekenen = '/bestel/afrekenen/%s/'      # bestel_nr
    url_check_status = '/bestel/check-status/%s/'           # bestel_nr
    url_na_de_betaling = '/bestel/na-de-betaling/%s/'       # bestel_nr
    url_annuleer_bestelling = '/bestel/annuleer/%s/'        # bestel_nr

    def setUp(self):
        """ initialisatie van de test case """

        self.functie_mww = Functie.objects.filter(rol='MWW').first()
        self.functie_mww.bevestigde_email = 'mww@bond.tst'
        self.functie_mww.save(update_fields=['bevestigde_email'])

        self.ver_extern = Vereniging.objects.get(ver_nr=settings.EXTERN_VER_NR)

        sporter = Sporter(
                        lid_nr=800001,
                        voornaam='Gast',
                        achternaam='Schutter',
                        geboorte_datum='1999-09-09',
                        sinds_datum='2023-03-03',
                        email='schutter@gast.net',
                        bij_vereniging=self.ver_extern,
                        is_gast=True,
                        postadres_1='##BUG: must not be used##')

        self.account_gast = self.e2e_create_account(str(sporter.lid_nr), sporter.email, sporter.voornaam)
        self.account_gast.is_gast = True
        self.account_gast.save(update_fields=['is_gast'])

        sporter.account = self.account_gast
        sporter.save()
        self.sporter = sporter

        gast = GastRegistratie(
                    lid_nr=1,
                    fase=REGISTRATIE_FASE_COMPLEET,
                    email=sporter.email,
                    email_is_bevestigd=True,
                    voornaam=sporter.voornaam,
                    achternaam=sporter.achternaam,
                    geboorte_datum=sporter.geboorte_datum,
                    eigen_lid_nummer=3333,
                    club='Eigen club',
                    club_plaats='Clib plaats',
                    wa_id='1234',
                    sporter=sporter,
                    account=self.account_gast)
        gast.save()

        now = timezone.now()

        mandje, is_created = BestelMandje.objects.get_or_create(account=self.account_gast)
        self.mandje = mandje

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='meervoud',
                        bestel_begrenzing='1-5',
                        prijs_euro="1.23")
        product.save()
        self.product = product

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=self.account_gast,
                        product=product,
                        aantal=1,
                        totaal_euro=Decimal('1.23'),
                        log='test')
        keuze.save()
        self.keuze = keuze

    def test_afleveradres(self):
        # bestelling door gastaccount met opgaaf afleveradres
        self.e2e_login(self.account_gast)

        # leg een webwinkel keuze in het mandje
        bestel_mutatieverzoek_webwinkel_keuze(self.account_gast, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties(kosten_pakket=10.42, kosten_brief=5.43)
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.prefetch_related('producten').first()
        self.assertEqual(str(bestelling.verzendkosten_euro), '10.42')
        self.assertEqual(1, bestelling.producten.count())
        product1 = bestelling.producten.filter(webwinkel_keuze=None).first()

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))
        self.assertTrue('Verzendkosten' in mail.mail_text)

        # bekijk de bestellingen
        with self.assert_max_queries(20):
            resp = self.client.get(self.url_bestellingen_overzicht)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestellingen.dtl', 'plein/site_layout.dtl'))

        # haal de details op
        url = self.url_bestelling_details % bestelling.bestel_nr
        with self.assert_max_queries(20):
            resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestel/toon-bestelling-details.dtl', 'plein/site_layout.dtl'))


# end of file
