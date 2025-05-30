# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helpers for testing via de browser """
from django.test import TestCase
from django.utils import timezone
from Account.models import Account
from BasisTypen.models import BoogType
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog,
                               CompetitieIndivKlasse, CompetitieMatch)
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon
from Sporter.models import Sporter, SporterBoog
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelFoto, WebwinkelProduct
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import datetime
import time
import json

coverage_data = dict()


def js_cov_add(data: str):
    data = json.loads(data)

    for fpath, cov_data in data.items():
        if fpath not in coverage_data:
            coverage_data[fpath] = list()

        for line_nr in cov_data.keys():
            if line_nr not in coverage_data[fpath]:
                coverage_data[fpath].append(line_nr)
        # for
    # for


def js_cov_save(fname):
    with open(fname, 'w') as f:
        f.write(json.dumps(coverage_data) + '\n')
        f.close()
    # with


class BrowserTestCase(TestCase):

    # deze members worden centraal gevuld in Plein/tests/test_js_in_browser
    sporter = None              # sporter 100001
    account = None              # account 424200 (gekoppeld aan sporter)
    ver = None                  # vereniging van de sporter
    functie_hwl = None          # account is hwl
    webwinkel_product = None    # product in de webwinkel
    match = None                # competitie match

    # urls voor do_navigate_to()
    url_plein = '/plein/'
    url_logout = '/account/logout/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'

    _driver = None
    live_server_url = ''

    lid_nr = 100001

    # browser interacties
    def get_console_log(self) -> list[str]:
        logs = self._driver.get_log('browser')
        regels = list()
        for log in logs:
            msg = log['message']
            if msg not in regels:
                regels.append(msg)
        return regels

    @staticmethod
    def get_following_sibling(element):
        return element.find_element(By.XPATH, "following-sibling::*[1]")

    @staticmethod
    def get_parent(element):
        return element.find_element(By.XPATH, "./..")

    def find_element_by_id(self, id_str):
        return self._driver.find_element(By.ID, id_str)

    def find_element_by_name(self, name_str):
        return self._driver.find_element(By.NAME, name_str)

    def find_element_type_with_text(self, elem_type, text_str):
        try:
            el = self._driver.find_element(By.XPATH, '//%s[text()="%s"]' % (elem_type, text_str))
        except NoSuchElementException:
            el = None
        return el

    def find_title(self):
        el = self._driver.find_element(By.XPATH, '//title')
        if el:
            return el.text
        return '?? title element not found ??'

    def find_tabel_filter_input(self, tabel_id):
        try:
            el_table = self._driver.find_element(By.ID, tabel_id)
        except NoSuchElementException:
            el_input = None
        else:
            # // = current node
            # input = tag name
            # @attribute = select
            #
            el_input = el_table.find_element(By.XPATH, '//input[@class="table-filter"]')
        return el_input

    def find_kaartje_met_titel(self, title):
        # geeft het kaartje element terug waarop geklikt kan worden
        # of None als niet gevonden

        # let op: record kaartjes hebben de titel in een span zitten --> a/div/span
        found = self._driver.find_elements(By.XPATH, '//a/div/div[@class="card-title"]')

        for div_title in found:
            # card is the div with the title
            if div_title.text == title:
                div_card = self.get_parent(div_title)
                a_href = self.get_parent(div_card)
                return a_href
        # for
        return None

    def wait_until_url_not(self, url: str, timeout: float = 2.0):
        duration = 0.5
        check_url = self.live_server_url + url
        curr_url = self._driver.current_url
        while curr_url == check_url and timeout > 0:
            time.sleep(duration)
            timeout -= duration
            duration *= 2
            curr_url = self._driver.current_url
        # while

    def do_navigate_to(self, url):
        # capture collected coverage before navigating away
        test = self._driver.execute_script('return JSON.stringify(_js_cov);')
        self._driver.get(self.live_server_url + url)
        js_cov_add(test)

    # helper functions
    def do_wissel_naar_hwl(self):
        # wissel naar rol HWL
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_%s' % self.functie_hwl.pk)    # radio button voor HWL
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)        # redirect naar /vereniging/

    def do_wissel_naar_bb(self):
        # wissel naar rol Manager MH
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90002')       # radio button voor Manager MH
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

    def do_wissel_naar_sporter(self):
        # wissel naar rol Sporter
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90000')       # radio button voor Sporter
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

    def do_logout(self):
        # uitloggen
        self.do_navigate_to(self.url_logout)
        h3 = self.find_element_type_with_text('h3', 'Uitloggen')
        self.assertIsNotNone(h3)

        self.find_element_by_id('submit_knop').click()
        self.wait_until_url_not(self.url_logout)

    def get_browser_cookie_value(self, cookie_name):
        return self._driver.get_cookie(cookie_name)['value']

    def get_page_html(self):
        return self._driver.page_source


# start een browser instantie
def get_driver(show_browser=False):
    options = ChromeOptions()

    # prevent using stored cookies
    options.add_argument('--incognito')

    # fixed window size, do not show
    if not show_browser:
        options.add_argument('--headless')

    options.add_argument('--window-size=1024,800')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    driver = Chrome(options=options)
    return driver


def database_vullen(self):
    lid_nr = BrowserTestCase.lid_nr

    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser
    Account.objects.filter(username=str(lid_nr)).delete()
    self.account = Account.objects.create(
                                username=str(lid_nr),
                                first_name='Bro',
                                last_name='dés Browser',
                                unaccented_naam='Bro des Browser',
                                bevestigde_email='bro@test.not',
                                email_is_bevestigd=True,
                                otp_code='whatever',
                                otp_is_actief=True,
                                is_BB=True)
    self.account.set_password(TEST_WACHTWOORD)
    self.account.save()

    self.vhpg = VerklaringHanterenPersoonsgegevens.objects.create(
                                                account=self.account,
                                                acceptatie_datum=timezone.now())

    self.rayon, _ = Rayon.objects.get_or_create(rayon_nr=5, naam="Rayon 5")
    self.regio, _ = Regio.objects.get_or_create(regio_nr=117, rayon_nr=self.rayon.rayon_nr, rayon=self.rayon)

    self.ver, _ = Vereniging.objects.get_or_create(
                                naam="Browser Club",
                                ver_nr=4200,
                                regio=self.regio)

    self.sporter, _ = Sporter.objects.get_or_create(
                                    lid_nr=lid_nr,
                                    geslacht="V",
                                    voornaam="Bro",
                                    achternaam="de Browser",
                                    geboorte_datum=datetime.date(year=1988, month=8, day=8),
                                    sinds_datum=datetime.date(year=2020, month=8, day=8),
                                    bij_vereniging=self.ver,
                                    account=self.account,
                                    email=self.account.email)

    self.boog_r, _ = BoogType.objects.get_or_create(
                                    afkorting='R',
                                    beschrijving='Recurve',
                                    volgorde=10)        # zelfde volgorde als het standaard object

    self.sporterboog, _ = SporterBoog.objects.get_or_create(
                                    sporter=self.sporter,
                                    boogtype=self.boog_r,
                                    voor_wedstrijd=True)

    self.functie_hwl, _ = Functie.objects.get_or_create(
                                rol='HWL',
                                beschrijving='HWL 4200',
                                bevestigde_email='hwl4200@test.not',
                                vereniging=self.ver)
    self.functie_hwl.accounts.add(self.account)

    # maak webwinkel producten aan
    foto = WebwinkelFoto()
    foto.save()

    self.foto1 = WebwinkelFoto(
                    locatie='gulden-1.png',
                    locatie_thumb='gulden-1_thumb.png')
    self.foto1.save()

    self.foto2 = WebwinkelFoto(
                    locatie='gulden-2.png',
                    locatie_thumb='gulden-2_thumb.png')
    self.foto2.save()

    product = WebwinkelProduct(
                    omslag_titel='Test product 1',
                    volgorde=1,
                    onbeperkte_voorraad=True,
                    omslag_foto=foto,
                    bestel_begrenzing='',
                    prijs_euro="1.23")
    product.save()
    product.fotos.add(self.foto1)
    product.fotos.add(self.foto2)
    self.webwinkel_product = product

    # maak een competitiewedstrijd aan waarop scores ingevoerd kunnen worden
    volgende_maand = timezone.now().date()
    volgende_maand += datetime.timedelta(days=31)

    self.comp = Competitie(
                        beschrijving='Indoor Test',
                        afstand=18,
                        begin_jaar=volgende_maand.year - 1)
    self.comp.save()

    self.klasse_indiv_r = CompetitieIndivKlasse(
                                competitie=self.comp,
                                boogtype=self.boog_r,
                                volgorde=1,
                                min_ag=0,
                                is_onbekend=True)
    self.klasse_indiv_r.save()

    self.match = CompetitieMatch(
                    competitie=self.comp,
                    beschrijving='Test match',
                    vereniging=self.ver,
                    datum_wanneer=volgende_maand,
                    tijd_begin_wedstrijd='20:00')
    self.match.save()

    self.regio_comp = Regiocompetitie(
                            competitie=self.comp,
                            regio=self.regio,
                            functie=self.functie_hwl)   # zou moeten zijn: RCL
    self.regio_comp.save()

    self.regio_ronde = RegiocompetitieRonde(
                            regiocompetitie=self.regio_comp,
                            week_nr=1,
                            beschrijving='Ronde 1')
    self.regio_ronde.save()
    self.regio_ronde.matches.add(self.match)

    self.regio_deelnemer = RegiocompetitieSporterBoog(
                                regiocompetitie=self.regio_comp,
                                sporterboog=self.sporterboog,
                                bij_vereniging=self.ver,
                                indiv_klasse=self.klasse_indiv_r)
    self.regio_deelnemer.save()


def database_opschonen(self):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser

    # LiveServerTestCase does not run inside a database transaction (like normal test cases)
    # so we have to clean up after ourselves
    self.regio_deelnemer.delete()
    self.regio_ronde.delete()
    self.match.delete()
    self.regio_comp.delete()
    self.klasse_indiv_r.delete()
    self.comp.delete()
    self.webwinkel_product.delete()
    self.foto1.delete()
    self.foto2.delete()
    self.functie_hwl.delete()
    self.sporterboog.delete()
    self.sporter.delete()
    self.vhpg.delete()
    self.account.delete()
    self.ver.delete()
    self.regio.delete()
    self.rayon.delete()
    self.boog_r.delete()


def populate_inst(self, inst):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser

    # load database object instances into the testcase instance
    inst.account = self.account
    inst.sporter = self.sporter
    inst.ver = self.ver
    inst.functie_hwl = self.functie_hwl
    inst.webwinkel_product = self.webwinkel_product
    inst.match = self.match

    # load members necessary for communication with the browser
    inst._driver = self._driver
    inst.live_server_url = self.live_server_url


# end of file
