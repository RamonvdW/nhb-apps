# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Bestelling.definities import (BESTELLING_STATUS_NIEUW, BESTELLING_STATUS_MISLUKT, BESTELLING_STATUS_GEANNULEERD,
                                   BESTELLING_STATUS_BETALING_ACTIEF)
from Bestelling.models import Bestelling
from Betaal.models import BetaalMutatie
from TestHelpers import browser_helper as bh
from TestHelpers.mgmt_cmds_helper import MyMgmtCommandHelper
import time


class TestBrowserBestellingAfrekenen(MyMgmtCommandHelper, bh.BrowserTestCase):

    """ Test de Bestelling applicatie, gebruik van bestelling_afrekenen.js vanuit de browser """

    url_mandje = '/bestel/mandje/'
    url_afrekenen = '/bestel/afrekenen/%s/'             # bestel_nr
    url_webwinkel_product = '/webwinkel/product-%s/'    # webwinkelproduct.pk
    url_bestelling_details = '/bestel/details/%s/'      # bestel_nr

    def test_bestelling_afrekenen(self):
        self.do_wissel_naar_sporter()       # redirect naar /plein/

        Bestelling.objects.all().delete()

        # leg een product in het mandje
        self.do_navigate_to(self.url_webwinkel_product % self.webwinkel_product.pk)
        knop = self.find_element_type_with_text('button', 'Leg in mijn mandje')
        knop.click()
        time.sleep(0.5)

        # mandje omzetten in een bestelling
        self.do_navigate_to(self.url_mandje)
        knop = self.find_element_type_with_text('button', 'Bestelling afronden')
        knop.click()
        # JS script stuurt een POST (form)
        # POST handler in view_mandje.py maakt mutatie voor de achtergrondtaak en wacht tot deze opgepikt is
        # achtergrondtaak verwerkt de taak maakt de bestelling (+stuurt e-mail)
        # POST handler stuurt gebruiker door naar overzicht van alle bestellingen
        time.sleep(0.5)

        # pik de aangemaakte bestelling op en ga naar de betaal pagina
        bestelling = Bestelling.objects.first()
        bestelling_url = self.url_bestelling_details % bestelling.bestel_nr
        self.do_navigate_to(bestelling_url)

        # klik op de knop om de betaling op te starten
        knop = self.find_element_type_with_text('button', 'Betalen')
        self.click_not_blocking(knop)

        # knop doet een POST (form)
        # deze toont een pagina en JS script begint status te pollen via een POST naar dynamische status view
        betaal_url = self.wait_until_url_not(bestelling_url)

        # de POST handler ziet status=nieuw en maakt een mutatie aan voor de achtergrondtaak
        # achtergrondtaak vraagt om betaalverzoek (create payment) welke door CPSP websim_betaal afgehandeld wordt
        # websim_betaal geeft de checkout url terug; achtergrondtaak zet deze in de betaal mutatie
        # JS script haalt nieuwe status op, krijgt de checkout url en stuurt de browser daarheen
        # websim_betaal toont de betaal pagina met 4 keuzes

        # redirect naar simulatie-betaal-pagina volgt
        checkout_url = self.wait_until_url_not(betaal_url)

        el_knop_volledig_betalen = self.find_element_type_with_text('button', 'Volledig betalen')
        self.assertIsNotNone(el_knop_volledig_betalen)
        el_knop_volledig_betalen.click()

        # betaal simulator stuurt nu een CPSP reactie naar de betaal achtergrondtaak
        # deze verwerkt de betaling en zet deze op 'betaald'
        # browser wordt doorgestuurd naar de "na-de-betaling" pagina (bestelling-afgerond.dtl)
        self.wait_until_url_not(checkout_url)

        # betaling nieuw --> mislukt
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(betaal_url)
        bestelling.status = BESTELLING_STATUS_MISLUKT
        bestelling.save(update_fields=['status'])
        time.sleep(0.5)        # eerste status check is na 250ms
        el_bericht = self.find_element_by_id('id_bericht')
        self.assertEqual(el_bericht.text, 'De betaling is niet gelukt')

        # betaling nieuw --> actief (zonder betaal mutatie) --> error
        bestelling.betaal_mutatie = None
        bestelling.status = BESTELLING_STATUS_BETALING_ACTIEF
        bestelling.save(update_fields=['betaal_mutatie', 'status'])
        self.do_navigate_to(betaal_url)
        time.sleep(0.5)        # eerste status check is na 250ms
        el_bericht = self.find_element_by_id('id_bericht')
        self.assertEqual(el_bericht.text, 'Er is een probleem opgetreden met deze bestelling')

        # betaling nieuw --> geannuleerd --> geeft 404 + exception in JSON parsing in JS
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(betaal_url)
        bestelling.status = BESTELLING_STATUS_GEANNULEERD
        bestelling.save(update_fields=['status'])
        time.sleep(1.5)         # eerste status check is na 250ms, daarna herhaling na 1 sec
        el_bericht = self.find_element_by_id('id_bericht')
        self.assertEqual(el_bericht.text, 'Het is op dit moment niet mogelijk om te betalen. Probeer het later nog eens')

        # test afhandeling van timeouts
        self.set_short_xhr_timeouts()
        bestelling.status = BESTELLING_STATUS_NIEUW
        bestelling.save(update_fields=['status'])
        self.do_navigate_to(betaal_url)
        time.sleep(0.5)     # eerste check wordt na 250ms gedaan

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()


# end of file
