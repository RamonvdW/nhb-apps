# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Bestelling.definities import BESTELLING_TRANSPORT_NVT
from Bestelling.models import BestellingMandje, Bestelling
from Bestelling.operations import bestel_mutatieverzoek_webwinkel_keuze
from Functie.models import Functie
from Mailer.models import MailQueue
from Registreer.definities import REGISTRATIE_FASE_COMPLEET
from Registreer.models import GastRegistratie
from Sporter.models import Sporter
from TestHelpers.e2ehelpers import E2EHelpers
from Vereniging.models import Vereniging
from Webwinkel.definities import VERZENDKOSTEN_PAKKETPOST
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from decimal import Decimal


class TestBestellingGast(E2EHelpers, TestCase):

    """ tests voor de Bestelling  applicatie, module bestellingen door gast account """

    test_after = ('Bestelling.tests.test_mandje', 'Bestelling.tests.test_bestelling', 'Registreer.tests.test_gast')

    url_mandje_bestellen = '/bestel/mandje/'
    url_afleveradres = '/bestel/mandje/afleveradres/'
    url_bestellingen_overzicht = '/bestel/overzicht/'

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

        mandje, is_created = BestellingMandje.objects.get_or_create(account=self.account_gast)
        self.mandje = mandje

        product = WebwinkelProduct(
                        omslag_titel='Test titel 1',
                        onbeperkte_voorraad=False,
                        aantal_op_voorraad=10,
                        eenheid='meervoud',
                        bestel_begrenzing='1-5',
                        prijs_euro=Decimal(1.23),
                        type_verzendkosten=VERZENDKOSTEN_PAKKETPOST)
        product.save()
        self.product = product

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        product=product,
                        aantal=1,
                        log='test')
        keuze.save()
        self.keuze = keuze

    def test_afleveradres(self):
        # bestelling door gastaccount met opgaaf afleveradres
        self.e2e_login(self.account_gast)

        # leg een webwinkel keuze in het mandje
        bestel_mutatieverzoek_webwinkel_keuze(self.account_gast, self.keuze, snel=True)
        self.verwerk_bestel_mutaties()

        # probeer het mandje om te zetten in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert404(resp, 'Afleveradres onbekend')

        self.mandje.refresh_from_db()
        self.assertEqual(self.mandje.afleveradres_regel_1, '')
        self.assertEqual(self.mandje.afleveradres_regel_2, '')
        self.assertEqual(self.mandje.afleveradres_regel_3, '')
        self.assertEqual(self.mandje.afleveradres_regel_4, '')
        self.assertEqual(self.mandje.afleveradres_regel_5, '')

        with self.assert_max_queries(20):
            resp = self.client.get(self.url_afleveradres)
        self.assertEqual(resp.status_code, 200)     # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/kies-afleveradres.dtl', 'design/site_layout.dtl'))

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afleveradres)
        self.assert_is_redirect(resp, self.url_mandje_bestellen)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afleveradres, {'regel1': 'Adresregel1',
                                                            'regel2': '',               # wordt overgeslagen
                                                            'regel3': 'Adresregel3',
                                                            'regel4': 'Adresregel4',
                                                            'regel5': 'Adresregel5'})
        self.assert_is_redirect(resp, self.url_mandje_bestellen)

        self.mandje.refresh_from_db()
        self.assertEqual(self.mandje.afleveradres_regel_1, 'Adresregel1')
        self.assertEqual(self.mandje.afleveradres_regel_2, 'Adresregel3')
        self.assertEqual(self.mandje.afleveradres_regel_3, 'Adresregel4')
        self.assertEqual(self.mandje.afleveradres_regel_4, 'Adresregel5')
        self.assertEqual(self.mandje.afleveradres_regel_5, '')

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_afleveradres, {'regel1': 'Adresregel1',
                                                            'regel2': 'Adresregel2',
                                                            'regel3': 'Adresregel3',
                                                            'regel4': 'Adresregel4',
                                                            'regel5': 'Adresregel5'})
        self.assert_is_redirect(resp, self.url_mandje_bestellen)

        # zet het mandje om in een bestelling
        self.assertEqual(0, Bestelling.objects.count())
        resp = self.client.post(self.url_mandje_bestellen, {'snel': 1})
        self.assert_is_redirect(resp, self.url_bestellingen_overzicht)
        self.verwerk_bestel_mutaties(kosten_pakket=10.42, kosten_brief=5.43)
        self.assertEqual(1, Bestelling.objects.count())

        self.assertEqual(1, MailQueue.objects.count())
        mail = MailQueue.objects.first()
        self.assert_email_html_ok(mail, 'email_bestelling/bevestig-bestelling.dtl')
        self.assert_consistent_email_html_text(mail, ignore=('>Bedrag:', '>Korting:'))
        # self.e2e_show_email_in_browser(mail)
        self.assertTrue('Verzendkosten' in mail.mail_text)
        self.assertTrue('8,68' in mail.mail_text)       # 1,23 + 7,45 verzendkosten = 8,68

        self.assertTrue('Adresregel1' in mail.mail_text)
        self.assertTrue('Adresregel2' in mail.mail_text)
        self.assertTrue('Adresregel3' in mail.mail_text)
        self.assertTrue('Adresregel4' in mail.mail_text)
        self.assertTrue('Adresregel5' in mail.mail_text)

    def test_cornercases(self):
        self.e2e_login(self.account_gast)

        # corner case: geen transport
        self.mandje.transport = BESTELLING_TRANSPORT_NVT
        self.mandje.save(update_fields=['transport'])
        resp = self.client.get(self.url_afleveradres)
        self.assert404(resp, 'Niet van toepassing')

        # corner case: geen mandje
        self.mandje.delete()
        resp = self.client.get(self.url_afleveradres)
        self.assert404(resp, 'Mandje is leeg')

        resp = self.client.post(self.url_afleveradres)
        self.assert404(resp, 'Mandje is leeg')

    def test_geen_gast(self):
        self.sporter.is_gast = False
        self.sporter.save(update_fields=['is_gast'])

        self.account_gast.is_gast = False
        self.account_gast.save(update_fields=['is_gast'])

        self.e2e_login(self.account_gast)

        resp = self.client.get(self.url_afleveradres)
        self.assert404(resp, 'Geen toegang')

        resp = self.client.post(self.url_afleveradres)
        self.assert404(resp, 'Geen toegang')


# end of file
