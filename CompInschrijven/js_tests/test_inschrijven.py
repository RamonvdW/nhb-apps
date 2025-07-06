# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.definities import INSCHRIJF_METHODE_1
from Competitie.test_utils.tijdlijn import zet_competitie_fase_regio_inschrijven
from TestHelpers import browser_helper as bh


class TestBrowserCompInschrijven(bh.BrowserTestCase):

    url_sporter_aanmelden = '/bondscompetities/deelnemen/aanmelden/%s/%s/bevestig/'  # deelcomp_pk, sporterboog_pk

    def test_inschrijven_sporter(self):
        # inloggen en als sporter de site gebruiken
        self.do_pass_otp()
        self.do_wissel_naar_sporter()

        # zet inschrijfmethode 1
        self.regio_comp.inschrijf_methode = INSCHRIJF_METHODE_1
        self.regio_comp.save(update_fields=['inschrijf_methode'])

        zet_competitie_fase_regio_inschrijven(self.comp)
        self.regio_deelnemer_r.delete()       # uitschrijven

        # haal de inschrijf pagina op
        url = self.url_sporter_aanmelden % (self.regio_comp.pk, self.sporterboog_r.pk)
        self.do_navigate_to(url)

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        # zet checkmarks in alle checkboxes
        for el in self.find_elements_checkbox():
            if el.text:
                self.click_if_possible(el)
        # for

        # toon 2e keus wedstrijden
        self.find_element_type_with_text('button', 'Toon meer wedstrijden').click()

        # zet checkmarks in alle checkboxes
        el_check = list()
        for el in self.find_elements_checkbox(exclude_selected=True):
            el_check.append(el)
            self.click_if_possible(el)
        # for

        # controleer dat de submit knop niet bruikbaar is
        # (omdat er meer dan 7 wedstrijden gekozen zijn)
        knop = self.find_element_by_id('submit_knop')
        self.assertIsNotNone(knop.get_attribute('disabled'))

        # verwijder een paar checkmarks
        # (bij maximaal 7 wedstrijden wordt de submit knop weer bruikbaar)
        for el in el_check[-2:]:
            self.click_if_possible(el)
        # for

        # check dat er geen fouten waren
        self.assert_no_console_log()

        # doe de inschrijving
        self.assertIsNone(knop.get_attribute('disabled'))
        knop.click()


# end of file
