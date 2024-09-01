# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from django.utils import timezone
from Bestelling.definities import BESTELLING_STATUS_BETALING_ACTIEF, BESTELLING_STATUS_AFGEROND
from Bestelling.models import BestellingProduct, Bestelling, BestellingMutatie
from Betaal.models import BetaalInstellingenVereniging
from Functie.models import Functie
from Geo.models import Regio
from Mailer.models import MailQueue
from Sporter.models import Sporter
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelProduct, WebwinkelKeuze
from TestHelpers.e2ehelpers import E2EHelpers
from decimal import Decimal


class TestBestelBetaling(E2EHelpers, TestCase):

    """ tests voor de applicatie Bestel: verstuur mail backoffice Webwinkel """

    test_after = ('Bestelling.tests.test_betaling', 'Bestelling.tests.test_overboeking')

    url_overboeking_ontvangen = '/bestel/vereniging/overboeking-ontvangen/'
    bestel_nr = 1234

    def setUp(self):
        """ initialisatie van de test case """

        self.account_admin = account = self.e2e_create_account_admin()
        self.account_admin.is_BB = True
        self.account_admin.save()
        self.account_email = 'admin@test.com'

        self.functie_mww = Functie.objects.get(rol='MWW')       # bestaat altijd
        self.functie_mww.bevestigde_email = 'webwinkel@hoofdkantoor'
        self.functie_mww.save(update_fields=['bevestigde_email'])

        instellingen = BetaalInstellingenVereniging(
                            vereniging=self.functie_mww.vereniging,
                            akkoord_via_bond=False)
        instellingen.save()
        self.instellingen = instellingen

        ver = Vereniging(
                ver_nr=1000,
                naam="Grote Club",
                regio=Regio.objects.get(regio_nr=112))
        ver.save()
        self.ver1 = ver

        sporter = Sporter(
            lid_nr=100000,
            voornaam='Ad',
            achternaam='de Admin',
            geboorte_datum='1966-06-06',
            sinds_datum='2020-02-02',
            account=account,
            bij_vereniging=ver,
            postadres_1='Grote weg 1',
            postadres_2='12345 Plaats',
            postadres_3='Buitenland')
        sporter.save()
        self.sporter = sporter

        product = WebwinkelProduct()
        product.save()

        now = timezone.now()

        keuze = WebwinkelKeuze(
                        wanneer=now,
                        koper=account,
                        product=product,
                        totaal_euro=Decimal(10.0),
                        log='test\n')
        keuze.save()
        self.webwinkel_keuze = keuze

        product = BestellingProduct(
            webwinkel_keuze=keuze,
            prijs_euro=Decimal(10.0))
        product.save()

        bestelling = Bestelling(
                        bestel_nr=self.bestel_nr,
                        account=self.account_admin,
                        ontvanger=instellingen,
                        verkoper_naam='Grote club',
                        verkoper_adres1='Adres 1',
                        verkoper_adres2='Adres 2',
                        verkoper_kvk='Kvk',
                        verkoper_email='contact@grote.club',
                        verkoper_telefoon='0123456789',
                        verkoper_iban='NL2BANK0123456789',
                        verkoper_bic='VER2BIC',
                        verkoper_heeft_mollie=False,
                        totaal_euro='10.00',
                        status=BESTELLING_STATUS_BETALING_ACTIEF,
                        log='Een beginnetje\n')
        bestelling.save()
        bestelling.producten.add(product)
        self.bestelling = bestelling

    def test_mail_backoffice(self):
        self.e2e_login_and_pass_otp(self.account_admin)
        self.e2e_wissel_naar_functie(self.functie_mww)
        self.e2e_check_rol('MWW')

        self.assertEqual(0, MailQueue.objects.count())
        self.assertEqual(0, self.bestelling.transacties.count())
        self.assertEqual(self.bestelling.status, BESTELLING_STATUS_BETALING_ACTIEF)

        with self.assert_max_queries(20):
            resp = self.client.post(self.url_overboeking_ontvangen,
                                    {'kenmerk': self.bestel_nr, 'bedrag': '10,00', 'actie': 'registreer', 'snel': '1'})
        self.assertEqual(resp.status_code, 200)  # 200 = OK
        self.assert_html_ok(resp)
        self.assert_template_used(resp, ('bestelling/overboeking-ontvangen.dtl', 'plein/site_layout.dtl'))

        self.assertEqual(1, BestellingMutatie.objects.count())
        f1, f2 = self.verwerk_bestel_mutaties()
        # print('\nf1: %s\nf2: %s' % (f1.getvalue(), f2.getvalue()))
        self.assertTrue("[INFO] Overboeking 10.00 euro ontvangen voor bestelling MH-%s" % self.bestel_nr
                        in f2.getvalue())
        self.assertTrue("[INFO] Betaling is gelukt voor bestelling MH-%s" % self.bestel_nr in f2.getvalue())
        self.bestelling = Bestelling.objects.get(pk=self.bestelling.pk)
        self.assertEqual(self.bestelling.status, BESTELLING_STATUS_AFGEROND)
        self.assertEqual(1, self.bestelling.transacties.count())
        # transactie = self.bestelling.transacties.first()

        self.assertEqual(2, MailQueue.objects.count())

        # controleer de betalingsbevestiging
        mail = MailQueue.objects.filter(mail_to=self.account_email)[0]
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)

        mail = MailQueue.objects.exclude(pk=mail.pk)[0]
        # print(mail.mail_text)
        # print(mail.mail_html.replace('<', '\n<'))
        self.assert_email_html_ok(mail)
        self.assert_consistent_email_html_text(mail)
        self.assertEqual(mail.mail_to, self.functie_mww.bevestigde_email)

# end of file
