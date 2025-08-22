# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.test import TestCase
from django.core.management.base import OutputWrapper
from django.utils import timezone
from Bestelling.definities import BESTELLING_STATUS_AFGEROND, BESTELLING_TRANSPORT_VERZEND, BESTELLING_TRANSPORT_OPHALEN
from Bestelling.models import BestellingMandje, Bestelling
from Bestelling.operations import (bestel_mutatieverzoek_webwinkel_keuze, bestel_mutatieverzoek_maak_bestellingen,
                                   stuur_email_webwinkel_backoffice, bestel_overboeking_ontvangen)
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from TestHelpers.betaal_sim import fake_betaling
from Vereniging.models import Vereniging
from Webwinkel.definities import VERZENDKOSTEN_BRIEFPOST
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal
import io


class TestBestellingBackoffice(E2EHelpers, TestCase):

    """ tests voor de applicatie Webwinkel: mail naar backoffice, na betaling """

    test_after = ('Bestelling.tests.test_bestelling',)

    email_backoffice = 'backoffice@khsn.not'

    def setUp(self):
        """ initialisatie van de test case """

        functie_mww = Functie.objects.get(rol='MWW')
        functie_mww.bevestigde_email = self.email_backoffice
        functie_mww.save(update_fields=['bevestigde_email'])

        ver = Vereniging(
                    ver_nr=1000,
                    naam="Grote Club",
                    regio=Regio.objects.get(regio_nr=112))
        ver.save()

        self.account_normaal = self.e2e_create_account('100000', 'normaal@test.com', 'Normaal')

        sporter = Sporter(
                        lid_nr=100000,
                        voornaam='Nor',
                        achternaam='Maal',
                        geboorte_datum='1977-07-07',
                        sinds_datum='2023-04-05',
                        account=self.account_normaal,
                        bij_vereniging=ver,
                        postadres_1='Doelpak baan 12',
                        postadres_2='Appartement 10',
                        postadres_3='1234XY Boogstad')
        sporter.save()
        self.sporter = sporter

        product1 = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        volgorde=1,
                        onbeperkte_voorraad=True,
                        bestel_begrenzing='',
                        prijs_euro="1.23")
        product1.save()
        self.product1 = product1

        keuze = WebwinkelKeuze(
                        wanneer=timezone.now(),
                        product=product1,
                        aantal=1)
        keuze.save()
        self.keuze1 = keuze

        product2 = WebwinkelProduct(
                        omslag_titel='Test titel 2',
                        volgorde=2,
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='doos,dozen',
                        bestel_begrenzing='1-20',
                        prijs_euro="42.00")
        product2.save()

        keuze = WebwinkelKeuze(
                        wanneer=timezone.now(),
                        product=product2,
                        aantal=2)
        keuze.save()
        self.keuze2 = keuze

        ver_bond = Vereniging(
                        ver_nr=settings.BETAAL_VIA_BOND_VER_NR,
                        naam='Bondsbureau',
                        plaats='Schietstad',
                        kvk_nummer='kvk1234',
                        contact_email='webwinkel@khsn.not',
                        telefoonnummer='0123456789',
                        regio=Regio.objects.get(regio_nr=100))
        ver_bond.save()
        self.ver_bond = ver_bond

        instellingen = BetaalInstellingenVereniging(
                            vereniging=ver_bond,
                            mollie_api_key='test_1234')
        instellingen.save()
        self.instellingen_bond = instellingen

        self.mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_normaal)

    def test_pakketpost(self):
        self.e2e_login(self.account_normaal)

        # leg twee webwinkel producten in het mandje en zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)     # !is_created
        self.verwerk_bestel_mutaties()

        self.mandje.refresh_from_db()
        self.mandje.afleveradres_regel_1 = self.sporter.postadres_1
        self.mandje.afleveradres_regel_2 = self.sporter.postadres_2
        self.mandje.afleveradres_regel_3 = self.sporter.postadres_3
        self.mandje.save()

        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.first()
        fake_betaling(bestelling, self.instellingen_bond)
        self.verwerk_bestel_mutaties()
        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, bestelling.transacties.count())

        # controleer de mail naar het backoffice
        self.assertEqual(MailQueue.objects.count(), 3)      # 1=bevestig bestelling, 2=bevestig betaling, 3=backoffice
        mail = MailQueue.objects.filter(mail_to=self.email_backoffice).first()
        # self.e2e_show_email_in_browser(mail)
        self.assert_email_html_ok(mail, 'email_bestelling/backoffice-versturen.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Korting:', 'Verenigingskorting: 50%<', 'Betaling:'))

        self.assertTrue(self.sporter.postadres_1 in mail.mail_text)
        self.assertTrue(self.sporter.postadres_2 in mail.mail_text)
        self.assertTrue(self.sporter.postadres_3 in mail.mail_text)

    def test_briefpost(self):
        # het enige product that we gaan kopen kan per brief verstuurd worden
        self.product1.type_verzendkosten = VERZENDKOSTEN_BRIEFPOST
        self.product1.save(update_fields=['type_verzendkosten'])

        self.e2e_login(self.account_normaal)
        self.assertEqual(0, Bestelling.objects.count())
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)

        self.verwerk_bestel_mutaties(kosten_brief=9.87)
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        self.assertEqual(bestelling.transport, BESTELLING_TRANSPORT_VERZEND)

    def test_ophalen(self):
        self.e2e_login(self.account_normaal)

        # leg twee webwinkel producten in het mandje en zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        self.verwerk_bestel_mutaties()

        self.mandje.refresh_from_db()
        self.mandje.transport = BESTELLING_TRANSPORT_OPHALEN
        self.mandje.save()

        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())

        bestelling = Bestelling.objects.first()
        fake_betaling(bestelling, self.instellingen_bond)
        self.verwerk_bestel_mutaties()
        bestelling.refresh_from_db()
        self.assertEqual(bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, bestelling.transacties.count())

        # controleer de mail naar het backoffice
        self.assertEqual(MailQueue.objects.count(), 3)      # 1=bevestig bestelling, 2=bevestig betaling, 3=backoffice
        mail = MailQueue.objects.filter(mail_to=self.email_backoffice).first()
        # self.e2e_show_email_in_browser(mail)
        self.assert_email_html_ok(mail, 'email_bestelling/backoffice-versturen.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Korting:', 'Verenigingskorting: 50%<', 'Betaling:'))

        self.assertTrue("Ophalen op het bondsbureau" in mail.mail_text)

    def test_email(self):
        # 3 soorten BTW en alle adresregels
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()

        bestelling.afleveradres_regel_1 = 'regel 1'
        bestelling.afleveradres_regel_2 = 'regel 2'
        bestelling.afleveradres_regel_3 = 'regel 3'
        bestelling.afleveradres_regel_4 = 'regel 4'
        bestelling.afleveradres_regel_5 = 'regel 5'

        bestelling.btw_percentage_cat1 = '1,42'
        bestelling.btw_percentage_cat2 = '8,6'
        bestelling.btw_percentage_cat3 = '25'

        bestelling.btw_euro_cat1 = Decimal(1)
        bestelling.btw_euro_cat2 = Decimal(2)
        bestelling.btw_euro_cat3 = Decimal(3)
        bestelling.save()

        MailQueue.objects.all().delete()
        stdout = OutputWrapper(io.StringIO())
        stuur_email_webwinkel_backoffice(stdout, bestelling)
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/backoffice-versturen.dtl')
        # self.e2e_show_email_in_browser(mail)

        self.assertTrue("Waarvan BTW 1,42%" in mail.mail_text)
        self.assertTrue("Waarvan BTW 8,6%" in mail.mail_text)
        self.assertTrue("Waarvan BTW 25%" in mail.mail_text)
        self.assertTrue("1,00" in mail.mail_text)
        self.assertTrue("2,00" in mail.mail_text)
        self.assertTrue("3,00" in mail.mail_text)
        self.assertTrue('regel 1' in mail.mail_text)
        self.assertTrue('regel 2' in mail.mail_text)
        self.assertTrue('regel 3' in mail.mail_text)
        self.assertTrue('regel 4' in mail.mail_text)
        self.assertTrue('regel 5' in mail.mail_text)

    def test_overboeking(self):
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze1, snel=True)
        bestel_mutatieverzoek_webwinkel_keuze(self.account_normaal, self.keuze2, snel=True)
        bestel_mutatieverzoek_maak_bestellingen(self.account_normaal, snel=True)
        self.verwerk_bestel_mutaties()
        self.assertEqual(1, Bestelling.objects.count())
        bestelling = Bestelling.objects.first()
        MailQueue.objects.all().delete()

        bestel_overboeking_ontvangen(bestelling, bestelling.totaal_euro, snel=True)
        self.verwerk_bestel_mutaties()

        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/backoffice-versturen.dtl')
        # self.e2e_show_email_in_browser(mail)


# end of file
