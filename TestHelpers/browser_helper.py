# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helpers for testing via de browser """
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from Account.models import Account
from BasisTypen.definities import GESLACHT_ALLE
from BasisTypen.models import BoogType, TeamType, Leeftijdsklasse
from Bestelling.models import BestellingMandje, BestellingHoogsteBestelNr
from Betaal.models import BetaalInstellingenVereniging
from Competitie.models import (Competitie, Regiocompetitie, RegiocompetitieRonde, RegiocompetitieSporterBoog,
                               CompetitieIndivKlasse, CompetitieTeamKlasse, CompetitieMatch)
from Functie.models import Functie, VerklaringHanterenPersoonsgegevens
from Geo.models import Regio, Rayon, Cluster
from Locatie.models import WedstrijdLocatie
from Score.models import Aanvangsgemiddelde
from Sporter.models import Sporter, SporterBoog
from Site.js_cov.js_cov_save import save_the_data, import_the_data
from TestHelpers.e2ehelpers import TEST_WACHTWOORD
from Vereniging.models import Vereniging
from Webwinkel.models import WebwinkelFoto, WebwinkelProduct
from Wedstrijden.definities import WEDSTRIJD_STATUS_GEACCEPTEERD
from Wedstrijden.models import Wedstrijd
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from bs4 import BeautifulSoup
import traceback
import datetime
import pyotp
import time
import json
import sys

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
    sporter: Sporter = None                                 # sporter 100001
    sporterboog_r: SporterBoog = None                       # sporterboog 100001, recurve
    sporterboog_bb: SporterBoog = None                      # sporterboog 100001, barebow
    account_bb: Account = None                              # account 100001 (gekoppeld aan sporter)
    account: Account = None                                 # account 100002
    ver: Vereniging = None                                  # vereniging van de sporter
    functie_hwl: Functie = None                             # account is hwl
    webwinkel_product: WebwinkelProduct = None              # product in de webwinkel
    comp: Competitie = None
    regio_comp: Regiocompetitie = None                      # regiocompetitie voor regio van sporter
    regio_match: CompetitieMatch = None
    regio_deelnemer_r: RegiocompetitieSporterBoog = None    # RegiocompetitieSporterBoog
    regio_deelnemer_bb: RegiocompetitieSporterBoog = None   # RegiocompetitieSporterBoog
    mandje: BestellingMandje = None
    wedstrijd_1: Wedstrijd = None
    locatie_outdoor = WedstrijdLocatie = None
    pause_after_console_log = 2

    # urls voor do_navigate_to()
    url_otp = '/account/otp-controle/'
    url_plein = '/plein/'
    url_login = '/account/login/'
    url_logout = '/account/logout/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'

    _driver = None
    _nav_hist = list()
    live_server_url = ''
    show_browser = False            # set to True for visibility during debugging

    lid_nr = 100001

    # state of the session
    session_state = "?"

    # browser interacties
    def get_console_log(self) -> list[str]:
        logs = self._driver.get_log('browser')      # gets the log + clears it!
        regels = list()
        for log in logs:                            # pragma: no cover
            # msg = log['message']
            msg = repr(log)
            if msg not in regels:
                regels.append(msg)
        return regels

    def assert_no_console_log(self):
        regels = self.get_console_log()
        if self.show_browser and len(regels) > 0 and self.pause_after_console_log > 0:      # pragma: no cover
            print('\n[ERROR] Unexpected console output:')
            for regel in regels:
                print(regel)
            # for
            print('[INFO] Sleeping for %s seconds' % self.pause_after_console_log)
            time.sleep(self.pause_after_console_log)
        self.assertEqual(regels, [])

    def get_following_sibling(self, element):
        self.assertIsNotNone(element)
        return element.find_element(By.XPATH, "following-sibling::*[1]")

    def get_parent(self, element):
        self.assertIsNotNone(element)
        return element.find_element(By.XPATH, "./..")

    def get_active_element(self):
        return self._driver.switch_to.active_element

    def find_element_by_id(self, id_str):
        # zoek op het "id" attribute van een element
        return self._driver.find_element(By.ID, id_str)

    def find_element_by_name(self, name_str):
        # zoek op het "name" attribute van een element
        return self._driver.find_element(By.NAME, name_str)

    def find_element_type_with_text(self, elem_type, text_str):
        try:
            return self._driver.find_element(By.XPATH, '//%s[text()="%s"]' % (elem_type, text_str))
        except NoSuchElementException:
            pass

        # walk all elements and check the text, which could be upper-cased
        text_str = text_str.upper()
        for el in self._driver.find_elements(By.TAG_NAME, elem_type):
            if el.text.upper() == text_str:
                return el
        # for

        return None

    def find_elements_buttons(self, must_have_id=True):
        buttons = list()
        for button in self._driver.find_elements(By.TAG_NAME, 'button'):
            id_str = button.get_attribute('id')
            if id_str:
                buttons.append(button)
        # for
        return buttons

    def find_elements_checkbox(self, exclude_selected=False):
        spans = list()
        for el in self._driver.find_elements(By.XPATH, '//input[@type="checkbox"]'):
            if exclude_selected and el.is_selected():
                continue
            span = self.get_following_sibling(el)
            spans.append(span)
        # for
        return spans

    def find_elements_radio(self, exclude_selected=False):
        spans = list()
        for el in self._driver.find_elements(By.XPATH, '//input[@type="radio"]'):
            if exclude_selected and el.is_selected():
                continue
            span = self.get_following_sibling(el)
            spans.append(span)
        # for
        return spans

    def find_elements_input(self, with_class=""):
        # example: with_class=".score-invoer"
        inputs = list()
        for inp in self._driver.find_elements(By.TAG_NAME, '//input[]%s' % with_class):
            inputs.append(inp)
        # for
        return inputs

    def find_elements_with_class(self, with_class: str):
        inputs = list()
        for inp in self._driver.find_elements(By.CLASS_NAME, with_class):
            inputs.append(inp)
        # for
        return inputs

    def find_title(self):
        return self._driver.title
        # el = self._driver.find_element(By.XPATH, '//title')
        # if el:
        #     return el.text
        # return '?? title element not found ??'

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
            el_input = el_table.find_element(By.XPATH, 'thead/tr/td/input[@class="table-filter"]')
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

    def find_active_button_on_open_modal_dialog(self):
        # wacht tot de animatie klaar is
        time.sleep(0.15)

        el = None
        try:
            dialog = self._driver.find_element(By.XPATH, '//div[@class="modal open"]')
        except NoSuchElementException:
            print('[ERROR] Could not find open modal dialog')
        else:
            buttons = list()
            for button in dialog.find_elements(By.TAG_NAME, 'button'):
                # skip de knop die alleen de dialog sluit
                if "modal-close" not in button.get_attribute('class'):
                    buttons.append(button)
            # for
            if len(buttons) != 1:
                msg = '[ERROR] Te veel knoppen op de modal dialog: %s; verwacht: 1' % len(buttons)
                for button in buttons:
                    msg += '\n     button.text = %s' % repr(button.text)
                # for
                self.fail(msg)
            else:
                el = buttons[0]

        return el

    @staticmethod
    def click_if_possible(el: WebElement):
        try:
            el.click()
        except ElementNotInteractableException:
            # waarschijnlijk hidden
            pass

    def click_not_blocking(self, el: WebElement):
        # el.click() seems to block until all events have been handled
        # action.click() does not wait
        pre_click = time.time()

        action = ActionChains(self._driver)
        action.click(el).perform()

        post_click = time.time()
        delta = post_click - pre_click
        self.assertLess(delta, 0.7)
        # print('click_not_blocking duration: %.3f' % delta)

    @staticmethod
    def debug_describe_element(el: WebElement):         # pragma: no cover
        msgs = list()

        tag = el.tag_name
        msgs.append('tag=%s' % repr(tag))

        text = el.text
        msgs.append('text=%s' % repr(text))

        attrs = ['id', 'name']

        if tag == 'input':
            attrs.append('type')
            attrs.append('hidden')

        for attr in attrs:
            val = el.get_attribute(attr)
            if val:
                msgs.append('%s=%s' % (attr, repr(val)))
        # for

        return ", ".join(msgs)

    def fetch_js_cov(self):
        # capture collected coverage before navigating away
        # the try-catch is to handle an exception that happens because window.localStorage does not yet exist
        # (no page loaded)
        script = 'try {\n'
        script += '  const data = localStorage.getItem("js_cov");\n'
        script += '  localStorage.removeItem("js_cov");\n'
        script += '  return data;\n'
        script += '} catch (e) {}\n'
        script += 'return "";\n'
        data = self._driver.execute_script(script)
        if data:                                            # pragma: no branch
            js_cov_add(data)

    def wait_until_url_not(self, url: str, timeout: float = 2.0):
        duration = 0.5
        if '://' not in url:
            url = self.live_server_url + url    # convert relative url into absolute url as reported back by browser
        curr_url = self._driver.current_url
        while curr_url == url and timeout > 0:
            time.sleep(duration)
            timeout -= duration
            duration *= 2
            curr_url = self._driver.current_url
        # while
        return self._driver.current_url.replace(self.live_server_url, '')

    def do_navigate_to(self, url, check_console_log=True):
        if check_console_log:
            # capture console output before loading a new page
            self.assert_no_console_log()

        # store invocation order
        found_frame = None
        for frame in traceback.extract_stack(limit=2):                              # pragma: no branch
            # print('frame: %s' % repr(frame))
            # interested frames contain /js_tests/, /tests/ or TestHelpers/browser_helper.py
            if "tests/" in frame.filename or "/TestHelpers/" in frame.filename:     # pragma: no branch
                found_frame = frame
                break
        # for

        # ga naar de nieuwe pagina - dit reset the globale variabele
        t1 = time.time()
        if self.show_browser:                   # pragma: no cover
            print('do_navigate_to:', url)
        self._driver.get(self.live_server_url + url)        # get() blocks until page is "loaded"
        t2 = time.time()
        if t2 - t1 > 1:                         # pragma: no cover
            # dat duurde meer dan 1 seconde
            print('\n[ERROR] HTTP GET took very long: %s seconds' % (t2 - t1))
            if len(self._nav_hist) > 0:
                prev_url, prev_frame = self._nav_hist[-1]
                print('        url = %s' % repr(url))
                if found_frame:
                    print('        caller:')
                    print("\n".join(traceback.format_list([found_frame])))
                else:
                    print('        caller: ???')
                print('        prev url = %s' % repr(prev_url))
                print('        caller:')
                print("\n".join(traceback.format_list([prev_frame])))

        if found_frame:
            self._nav_hist.append((url, found_frame))

    def do_login(self):
        # print('do_login: session_state=%s' % self.session_state)
        if self.session_state in ("logged in", "passed otp"):
            return

        # haal de inlog pagina op
        self.do_navigate_to(self.url_login, check_console_log=False)

        if self._driver.title == 'Inloggen':
            # gelukt
            self.assert_no_console_log()

            self._driver.find_element(By.ID, 'id_login_naam').send_keys(self.account_bb.username)
            self._driver.find_element(By.ID, 'id_wachtwoord').send_keys(TEST_WACHTWOORD)

            login_vink = self._driver.find_element(By.NAME, 'aangemeld_blijven')
            self.assertTrue(login_vink.is_selected())

            self._driver.find_element(By.ID, 'submit_knop').click()

            self.wait_until_url_not(self.url_login)        # gaat naar otp controle (want: is_BB)

        elif self._driver.title.startswith('MijnHandboogsport'):  # test server & dev hebben toevoeging
            # we zijn op het plein beland en waren dus al ingelogd
            pass

        self.session_state = "logged in"

    def do_pass_otp(self):
        # print('do_pass_otp: session_state=%s' % self.session_state)
        if self.session_state == "passed otp":
            return

        # zorg dat we ingelogd zijn
        self.do_login()

        # pass otp
        if self._driver.title != 'Controle tweede factor MijnHandboogsport':
            self.do_navigate_to(self.url_otp, check_console_log=False)
        self.assertEqual(self._driver.title, 'Controle tweede factor MijnHandboogsport')
        self.assert_no_console_log()

        otp_code = pyotp.TOTP(self.account_bb.otp_code).now()
        self._driver.find_element(By.ID, 'otp1').send_keys(otp_code)
        self._driver.find_element(By.ID, 'submit_knop').click()
        self.wait_until_url_not(self.url_otp)          # gaat naar wissel-van-rol

        self.session_state = "passed otp"

    def do_logout(self):
        # print('do_logout: session_state=%s' % self.session_state)
        if self.session_state == "logged out":
            return

        # ga naar de uitloggen pagina
        self.do_navigate_to(self.url_logout, check_console_log=False)

        if self._driver.title == 'Uitloggen':
            # we zijn op de uitloggen pagina beland
            h3 = self.find_element_type_with_text('h3', 'Uitloggen')
            self.assertIsNotNone(h3)

            self.find_element_by_id('submit_knop').click()
            self.wait_until_url_not(self.url_logout)

        elif self._driver.title.startswith('MijnHandboogsport'):        # test server & dev hebben toevoeging
            # we zijn op het plein beland en waren dus niet ingelogd
            pass

        self.session_state = "logged out"

    def do_wissel_naar_hwl(self):
        # wissel naar rol HWL
        self.do_pass_otp()
        if self._driver.title != 'Kies je rol':
            print('{do_wissel_naar_hwl} titel was %s. Ga naar wissel naar rol' % self._driver.title)
            self.do_navigate_to(self.url_wissel_van_rol, check_console_log=False)
        page = radio = ""
        try:
            radio = self.find_element_by_id('id_eigen_%s' % self.functie_hwl.pk)    # radio button voor HWL
        except NoSuchElementException:
            page = self.get_page_html()
        if page:
            self.fail('[ERROR] Failed to find radiobutton for HWL role! page:\n%s' % page)
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)        # redirect naar /vereniging/

    def do_wissel_naar_bb(self):
        # wissel naar rol Manager MH
        self.do_pass_otp()
        if self._driver.title != 'Kies je rol':
            print('{do_wissel_naar_bb} titel was %s. Ga naar wissel naar rol' % self._driver.title)
            self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90002')       # radio button voor Manager MH
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

    def do_wissel_naar_sporter(self):
        # wissel naar rol Sporter
        self.do_pass_otp()
        if self._driver.title != 'Kies je rol':
            print('{do_wissel_naar_sporter} titel was %s. Ga naar wissel naar rol' % self._driver.title)
            self.do_navigate_to(self.url_wissel_van_rol)
        radio = self.find_element_by_id('id_eigen_90000')       # radio button voor Sporter
        self.get_following_sibling(radio).click()
        self.find_element_by_id('activeer_eigen').click()       # activeer knop
        self.wait_until_url_not(self.url_wissel_van_rol)

    def get_browser_cookie_value(self, cookie_name):
        return self._driver.get_cookie(cookie_name)['value']

    def get_current_url(self):
        return self._driver.current_url

    def get_page_html(self):                                    # pragma: no cover
        content = self._driver.page_source
        soup = BeautifulSoup(content, features="html.parser")
        return soup.prettify()

    def set_short_xhr_timeouts(self):
        script = 'localStorage.setItem("js_cov_short_timeout", true);'
        self._driver.execute_script(script)

    def set_normal_xhr_timeouts(self):
        script = 'localStorage.removeItem("js_cov_short_timeout");'
        self._driver.execute_script(script)


# start een browser instantie
def get_driver(show_browser=False):
    options = ChromeOptions()

    # prevent using stored cookies
    options.add_argument('--incognito')

    # fixed window size, do not show
    if not show_browser:                        # pragma: no branch
        options.add_argument('--headless')

    options.add_argument('--window-size=1024,1200')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})

    # page load strategy: normal / eager / none
    # effect voor deze sequence: button click() --> script --> xhr post --> wacht 3 sec --> http response
    # normal: element.click() hangt 3 seconden :-(
    # eager: element.click() retourneert meteen, maar toch niet altijd :-(
    # options.page_load_strategy = 'none'

    driver = Chrome(options=options)
    return driver


def database_vullen(inst):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser
    lid_nr = BrowserTestCase.lid_nr
    lid_nr2 = lid_nr + 5

    inst.account_bb = Account.objects.create(
                                username=str(lid_nr),
                                first_name='Boss',
                                last_name='dés Browser',
                                unaccented_naam='Boss des Browser',
                                bevestigde_email='boss@test.not',
                                email_is_bevestigd=True,
                                otp_code='whatever',
                                otp_is_actief=True,
                                is_BB=True,             # geeft toegang tot rol Manager MH
                                is_staff=True)          # geeft toegang tot bepaalde kaartjes, zoals login-as
    inst.account_bb.set_password(TEST_WACHTWOORD)
    inst.account_bb.save()

    inst.vhpg = VerklaringHanterenPersoonsgegevens.objects.create(
                                                account=inst.account_bb,
                                                acceptatie_datum=timezone.now())

    Account.objects.filter(username=str(lid_nr + 1)).delete()
    inst.account = Account.objects.create(
                                username=str(lid_nr + 1),
                                first_name='Bro',
                                last_name='dés Browser',
                                unaccented_naam='Bro des Browser',
                                bevestigde_email='bro@test.not',
                                email_is_bevestigd=True)

    inst.rayon = Rayon.objects.create(rayon_nr=5, naam="Rayon 5")
    inst.regio = Regio.objects.create(regio_nr=117, rayon_nr=inst.rayon.rayon_nr, rayon=inst.rayon)

    inst.ver_bond = Vereniging.objects.create(
                            ver_nr=settings.WEBWINKEL_VERKOPER_VER_NR,
                            naam='Bondsbureau',
                            regio=inst.regio)

    inst.ontvanger = BetaalInstellingenVereniging.objects.create(
                            vereniging=inst.ver_bond,
                            mollie_api_key='test_1234')

    inst.cluster_117a = Cluster.objects.create(
                            regio=inst.regio,
                            letter='A',
                            naam='Cluster A',
                            gebruik='18')

    inst.cluster_117b = Cluster.objects.create(
                            regio=inst.regio,
                            letter='B',
                            naam='Cluster B',
                            gebruik='18')

    inst.ver = Vereniging.objects.create(
                            naam="Browser Club",
                            ver_nr=4200,
                            regio=inst.regio)
    inst.ver.clusters.add(inst.cluster_117a)

    inst.ver2 = Vereniging.objects.create(
                            naam="Browser Club 2",
                            ver_nr=4201,
                            regio=inst.regio)
    inst.ver.clusters.add(inst.cluster_117b)

    inst.sporter = Sporter.objects.create(
                                lid_nr=lid_nr,
                                geslacht="V",
                                voornaam="Froukje",
                                achternaam="de Browser",
                                unaccented_naam="Froukje de Browser",
                                geboorte_datum=datetime.date(year=1988, month=8, day=8),
                                sinds_datum=datetime.date(year=2020, month=8, day=8),
                                bij_vereniging=inst.ver,
                                account=inst.account_bb,
                                email=inst.account_bb.email,
                                postadres_1='Doelbaan 4',
                                postadres_2='9999ZZ Boogstad')

    inst.sporter2 = Sporter.objects.create(
                                    lid_nr=lid_nr2,
                                    geslacht="M",
                                    voornaam="Bro",
                                    achternaam="de Browser",
                                    unaccented_naam="Bro de Browser",
                                    geboorte_datum=datetime.date(year=2000, month=1, day=5),
                                    sinds_datum=datetime.date(year=2022, month=7, day=1),
                                    bij_vereniging=inst.ver,
                                    email='')

    inst.boog_r = BoogType.objects.create(
                                    afkorting='R',
                                    beschrijving='Recurve',
                                    volgorde=10)        # zelfde volgorde als het standaard object

    inst.boog_bb = BoogType.objects.create(
                                    afkorting='BB',
                                    beschrijving='Barebow',
                                    volgorde=12)        # zelfde volgorde als het standaard object

    inst.team_r = TeamType.objects.create(
                                    afkorting='R',
                                    beschrijving='Recurve Team',
                                    volgorde=1)
    inst.team_r.boog_typen.set([inst.boog_r])

    inst.sporterboog_r = SporterBoog.objects.create(
                                    sporter=inst.sporter,
                                    boogtype=inst.boog_r,
                                    voor_wedstrijd=True)

    inst.sporterboog_bb = SporterBoog.objects.create(
                                    sporter=inst.sporter,
                                    boogtype=inst.boog_bb,
                                    voor_wedstrijd=True)

    inst.sporterboog2_r = SporterBoog.objects.create(
                                    sporter=inst.sporter2,
                                    boogtype=inst.boog_r,
                                    voor_wedstrijd=True)

    inst.functie_hwl = Functie.objects.create(
                                rol='HWL',
                                beschrijving='HWL 4200',
                                bevestigde_email='hwl4200@test.not',
                                vereniging=inst.ver)
    inst.functie_hwl.accounts.add(inst.account_bb)

    inst.functie_mww, _ = Functie.objects.get_or_create(
                                rol='MWW')
    # override static object created by migrations
    inst.functie_mww.beschrijving = 'Manager Webwinkel'
    inst.functie_mww.bevestigde_email = 'mww@test.not'
    inst.functie_mww.save()

    inst.functie_mww.accounts.add(inst.account_bb)

    inst.functie_mwz = Functie.objects.create(
                                rol='MWZ',
                                beschrijving='Manager Wedstrijdzaken',
                                bevestigde_email='mwz@test.not')
    inst.functie_mwz.accounts.add(inst.account_bb)

    # maak webwinkel producten aan
    foto = WebwinkelFoto()
    foto.save()

    inst.foto1 = WebwinkelFoto.objects.create(
                    locatie='gulden-1.png',
                    locatie_thumb='gulden-1_thumb.png',
                    volgorde=1)

    inst.foto2 = WebwinkelFoto.objects.create(
                    locatie='gulden-2.png',
                    locatie_thumb='gulden-2_thumb.png',
                    volgorde=2)

    product = WebwinkelProduct.objects.create(
                    omslag_titel='Test product 1',
                    volgorde=1,
                    onbeperkte_voorraad=True,
                    omslag_foto=foto,
                    bestel_begrenzing='',
                    prijs_euro="1.23")
    product.fotos.add(inst.foto1)
    product.fotos.add(inst.foto2)
    inst.webwinkel_product = product

    inst.mandje = BestellingMandje.objects.create(
                    account=inst.account)

    BestellingHoogsteBestelNr(hoogste_gebruikte_bestel_nr=42000).save()

    # maak een competitiewedstrijd aan waarop scores ingevoerd kunnen worden
    volgende_maand = timezone.now().date()
    volgende_maand += datetime.timedelta(days=31)

    inst.lkl_all = Leeftijdsklasse.objects.create(
                        afkorting='Alle',
                        beschrijving='Alle',
                        klasse_kort='Alle',
                        wedstrijd_geslacht=GESLACHT_ALLE,
                        min_wedstrijdleeftijd=0,
                        max_wedstrijdleeftijd=99,
                        volgorde=1)

    inst.comp = Competitie(
                        beschrijving='Indoor Test',
                        afstand=18,
                        begin_jaar=volgende_maand.year - 1)
    inst.comp.save()
    inst.comp.boogtypen.add(inst.boog_r)        # noodzakelijk om in te kunnen schrijven
    inst.comp.refresh_from_db()                 # datum strings omgezet naar datetime object

    inst.klasse_indiv_r = CompetitieIndivKlasse.objects.create(
                                competitie=inst.comp,
                                boogtype=inst.boog_r,
                                volgorde=1,
                                min_ag=0,
                                is_onbekend=True)
    inst.klasse_indiv_r.leeftijdsklassen.add(inst.lkl_all)

    inst.klasse_indiv_bb = CompetitieIndivKlasse.objects.create(
                                competitie=inst.comp,
                                boogtype=inst.boog_bb,
                                volgorde=3,
                                min_ag=0,
                                is_onbekend=True)
    inst.klasse_indiv_bb.leeftijdsklassen.add(inst.lkl_all)

    inst.klasse_team_r = CompetitieTeamKlasse.objects.create(
                                competitie=inst.comp,
                                team_type=inst.team_r,
                                volgorde=1,
                                beschrijving="Recurve ERE",
                                min_ag=0.0,     # sporter heeft geen AG!
                                is_voor_teams_rk_bk=True)

    inst.regio_comp = Regiocompetitie.objects.create(
                            competitie=inst.comp,
                            regio=inst.regio,
                            functie=inst.functie_hwl)   # zou moeten zijn: RCL

    inst.regio_ronde = RegiocompetitieRonde.objects.create(
                            regiocompetitie=inst.regio_comp,
                            week_nr=1,
                            beschrijving='Ronde 1')

    inst.regio_match = CompetitieMatch.objects.create(
                        competitie=inst.comp,
                        beschrijving='Test match 1a',
                        vereniging=inst.ver,
                        datum_wanneer=volgende_maand,
                        tijd_begin_wedstrijd='20:00')
    inst.regio_ronde.matches.add(inst.regio_match)

    match = CompetitieMatch.objects.create(
                        competitie=inst.comp,
                        beschrijving='Test match 2a',
                        vereniging=inst.ver,
                        datum_wanneer=volgende_maand + datetime.timedelta(days=3),
                        tijd_begin_wedstrijd='20:01')
    inst.regio_ronde.matches.add(match)

    for lp in range(7):
        match = CompetitieMatch.objects.create(
                            competitie=inst.comp,
                            beschrijving='Test match %sb' % lp,
                            vereniging=inst.ver2,
                            datum_wanneer=volgende_maand,
                            tijd_begin_wedstrijd='19:00')
        inst.regio_ronde.matches.add(match)
    # for

    inst.regio_deelnemer_r = RegiocompetitieSporterBoog.objects.create(
                                    regiocompetitie=inst.regio_comp,
                                    sporterboog=inst.sporterboog_r,
                                    bij_vereniging=inst.sporterboog_r.sporter.bij_vereniging,
                                    indiv_klasse=inst.klasse_indiv_r,
                                    inschrijf_voorkeur_team=True,
                                    ag_voor_team_mag_aangepast_worden=True,
                                    ag_voor_team=7.0)

    inst.regio_deelnemer_bb = RegiocompetitieSporterBoog.objects.create(
                                    regiocompetitie=inst.regio_comp,
                                    sporterboog=inst.sporterboog_bb,
                                    bij_vereniging=inst.sporterboog_bb.sporter.bij_vereniging,
                                    indiv_klasse=inst.klasse_indiv_bb)

    inst.regio_deelnemer2_r = RegiocompetitieSporterBoog.objects.create(
                                    regiocompetitie=inst.regio_comp,
                                    sporterboog=inst.sporterboog2_r,
                                    bij_vereniging=inst.sporterboog2_r.sporter.bij_vereniging,
                                    indiv_klasse=inst.klasse_indiv_r,
                                    inschrijf_voorkeur_team=True,
                                    ag_voor_team=9.2)

    inst.ag = Aanvangsgemiddelde.objects.create(
                    sporterboog=inst.sporterboog_r,
                    boogtype=inst.boog_r,
                    afstand_meter=inst.comp.afstand,
                    waarde=8.0)

    # voeg een locatie toe
    inst.locatie_outdoor = WedstrijdLocatie(
                                baan_type='O',
                                naam='Vereniging outdoor locatie',
                                discipline_outdoor=True,
                                buiten_max_afstand=90,
                                buiten_banen=24)
    inst.locatie_outdoor.save()
    inst.locatie_outdoor.verenigingen.add(inst.ver_bond)
    inst.locatie_outdoor.verenigingen.add(inst.ver2)

    datum = timezone.now() + datetime.timedelta(days=30)
    if datum.day >= 29:  # pragma: no cover
        # zorg dat datum+1 dag in dezelfde maand is
        datum += datetime.timedelta(days=7)

    inst.wedstrijd_1 = Wedstrijd(
                        titel='Test 1',
                        status=WEDSTRIJD_STATUS_GEACCEPTEERD,
                        datum_begin=datum,
                        datum_einde=datum,
                        organiserende_vereniging=inst.ver,
                        locatie=inst.locatie_outdoor)
    inst.wedstrijd_1.save()


def database_opschonen(_inst):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser

    # LiveServerTestCase does not run inside a database transaction, like normal test cases
    # yet, we don't have to clean up after ourselves
    # LiveServerTestCase is based on a TransactionTestCase, which flushes all the database tables
    # at the end of the test run.
    # this unfortunately deletes all statically created objects (by squash migrations)
    return


def populate_inst(self, inst):
    # wordt aangeroepen vanuit Plein/tests/test_js_in_browser

    # load database object instances into the testcase instance
    inst.ver = self.ver
    inst.comp = self.comp
    inst.mandje = self.mandje
    inst.account = self.account
    inst.sporter = self.sporter
    inst.account_bb = self.account_bb
    inst.regio_comp = self.regio_comp
    inst.regio_match = self.regio_match
    inst.functie_hwl = self.functie_hwl
    inst.wedstrijd_1 = self.wedstrijd_1
    inst.sporterboog_r = self.sporterboog_r
    inst.sporterboog_bb = self.sporterboog_bb
    inst.locatie_outdoor = self.locatie_outdoor
    inst.regio_deelnemer_r = self.regio_deelnemer_r
    inst.regio_deelnemer_bb = self.regio_deelnemer_bb
    inst.webwinkel_product = self.webwinkel_product

    # load members necessary for communication with the browser
    inst._driver = self._driver
    inst._nav_hist = self._nav_hist
    inst.show_browser = self.show_browser
    inst.session_state = self.session_state
    inst.live_server_url = self.live_server_url
    inst.pause_after_console_log = self.pause_after_console_log


# end of file
