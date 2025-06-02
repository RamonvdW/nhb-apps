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
from Site.js_cov.js_cov_save import save_the_data, import_the_data
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelFoto, WebwinkelProduct
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import datetime
import pyotp
import time
import json

coverage_data = dict()


def js_cov_add(data: str):
    # print('js_cov_add: %s' % repr(data))
    data = json.loads(data)

    for fpath, cov_data in data.items():
        if fpath not in coverage_data:
            coverage_data[fpath] = list()

        for nr_str in cov_data.keys():
            line_nr = int(nr_str)
            if line_nr not in coverage_data[fpath]:
                coverage_data[fpath].append(line_nr)
        # for
    # for


def js_cov_save():
    # print('{js_cov} saving the data')
    save_the_data(coverage_data)


def js_cov_import():
    # print('{js_cov} importing the data')
    import_the_data()
    return 1


class BrowserTestCase(TestCase):

    # deze members worden centraal gevuld in Plein/tests/test_js_in_browser
    sporter = None              # sporter 100001
    account = None              # account 424200 (gekoppeld aan sporter)
    ver = None                  # vereniging van de sporter
    functie_hwl = None          # account is hwl
    webwinkel_product = None    # product in de webwinkel
    match = None                # competitie match

    # urls voor do_navigate_to()
    url_otp = '/account/otp-controle/'
    url_plein = '/plein/'
    url_login = '/account/login/'
    url_logout = '/account/logout/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'

    _driver = None
    live_server_url = ''
    show_browser = False            # set to True for visibility during debugging
    pause_after_console_log = 0     # seconden wachten als we een console error zien

    lid_nr = 100001

    # state of the session
    session_state = "?"

    # browser interacties
    def get_console_log(self) -> list[str]:
        logs = self._driver.get_log('browser')      # gets the log + clears it!
        regels = list()
        for log in logs:
            #msg = log['message']
            msg = repr(log)
            if msg not in regels:
                regels.append(msg)
        return regels

    def assert_no_console_log(self):
        regels = self.get_console_log()
        if self.show_browser and len(regels) > 0 and self.pause_after_console_log > 0:
            print('\n[ERROR] Unexpected console output:')
            for regel in regels:
                print(regel)
            # for
            print('[INFO] Sleeping for %s seconds' % self.pause_after_console_log)
            time.sleep(self.pause_after_console_log)
        self.assertEqual(regels, [])

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

    def fetch_js_cov(self):
        # capture collected coverage before navigating away
        script = 'if (window._js_cov !== undefined) {'
        script += 'const data = JSON.stringify(window._js_cov); window._js_cov = {}; return data;'
        script += '} else { return "{}"; }'
        test = self._driver.execute_script(script)
        js_cov_add(test)

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

    def do_login(self):
        # print('do_login: session_state=%s' % self.session_state)
        if self.session_state == "logged in":
            return

        # inloggen
        self._driver.get(self.live_server_url + self.url_login)
        self.assertEqual(self._driver.title, 'Inloggen')
        self.assert_no_console_log()

        self._driver.find_element(By.ID, 'id_login_naam').send_keys(self.account.username)
        self._driver.find_element(By.ID, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)
        login_vink = self._driver.find_element(By.NAME, 'aangemeld_blijven')
        self.assertTrue(login_vink.is_selected())
        self._driver.find_element(By.ID, 'submit_knop').click()
        self.wait_until_url_not(self.url_login)        # gaat naar otp control (want: is_BB)

        self.session_state = "logged in"

    def do_pass_otp(self):
        # print('do_pass_otp: session_state=%s' % self.session_state)
        if self.session_state == "passed otp":
            return

        # zorg dat we ingelogd zijn
        self.do_login()

        # pass otp
        self._driver.get(self.live_server_url + self.url_otp)
        self.assertEqual(self._driver.title, 'Controle tweede factor MijnHandboogsport')
        self.assert_no_console_log()

        otp_code = pyotp.TOTP(self.account.otp_code).now()
        self._driver.find_element(By.ID, 'id_otp_code').send_keys(otp_code)
        self._driver.find_element(By.ID, 'submit_knop').click()
        self.wait_until_url_not(self.url_otp)          # gaat naar wissel-van-rol

        self.session_state = "passed otp"

    def do_logout(self):
        # print('do_logout: session_state=%s' % self.session_state)
        if self.session_state == "logged out":
            return

        # uitloggen
        self.do_navigate_to(self.url_logout)
        h3 = self.find_element_type_with_text('h3', 'Uitloggen')
        self.assertIsNotNone(h3)

        self.find_element_by_id('submit_knop').click()
        self.wait_until_url_not(self.url_logout)

        self.session_state = "logged out"

    def do_navigate_to(self, url):
        # capture the coverage before it gets lost due to the page load
        self.fetch_js_cov()

        # controleer dat er geen meldingen van de browser zijn over de JS bestanden
        self.assert_no_console_log()

        # ga naar de nieuwe pagina - dit reset the globale variabele
        self._driver.get(self.live_server_url + url)

    def do_wissel_naar_hwl(self):
        # wissel naar rol HWL
        self.do_pass_otp()
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_%s' % self.functie_hwl.pk)    # radio button voor HWL
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)        # redirect naar /vereniging/

    def do_wissel_naar_bb(self):
        # wissel naar rol Manager MH
        self.do_pass_otp()
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90002')       # radio button voor Manager MH
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

    def do_wissel_naar_sporter(self):
        # wissel naar rol Sporter
        self.do_pass_otp()
        self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90000')       # radio button voor Sporter
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

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
                                    email=self.account.email)
    self.sporter.account = self.account
    self.sporter.save(update_fields=['account'])

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
                    locatie_thumb='gulden-1_thumb.png',
                    volgorde=1)
    self.foto1.save()

    self.foto2 = WebwinkelFoto(
                    locatie='gulden-2.png',
                    locatie_thumb='gulden-2_thumb.png',
                    volgorde=2)
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
    self.regio.delete()         # regio 117
    self.rayon.delete()         # rayon 5
    # self.boog_r.delete()


def populate_inst(self, inst):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser

    # load database object instances into the testcase instance
    inst.ver = self.ver
    inst.match = self.match
    inst.account = self.account
    inst.sporter = self.sporter
    inst.functie_hwl = self.functie_hwl
    inst.webwinkel_product = self.webwinkel_product

    # load members necessary for communication with the browser
    inst._driver = self._driver
    inst.show_browser = self.show_browser
    inst.session_state = self.session_state
    inst.live_server_url = self.live_server_url
    inst.pause_after_console_log = self.pause_after_console_log


# end of file
