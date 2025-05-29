# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helpers for testing via de browser """
from django.test import TestCase
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time


class BrowserTestCase(TestCase):

    # deze members worden centraal gevuld in Plein/tests/test_js_in_browser
    account = None      # account van de sporter
    sporter = None      # sporter zelf
    regio = None        # regio 117
    rayon = None        # rayon 5
    ver = None          # vereniging van de sporter
    functie_hwl = None  # sporter is HWL
    vhpg = None         # vhpg is geaccepteerd

    # urls voor do_navigate_to()
    url_plein = '/plein/'
    url_logout = '/account/logout/'
    url_wissel_van_rol = '/functie/wissel-van-rol/'

    _driver = None
    live_server_url = ''

    # browser interacties
    def get_console_log(self) -> list[str]:
        logs = self._driver.get_log('browser')
        regels = list()
        for log in logs:
            msg = log['message']
            if msg not in regels:
                regels.append(msg)
        return regels

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

    def find_tabel_filter_input(self, tabel_id):
        try:
            el_table = self._driver.find_element(By.ID, tabel_id)
        except NoSuchElementException:
            el_input = None
        else:
            el_input = el_table.find_element(By.XPATH, '//input[@class="table-filter"]')
        return el_input

    @staticmethod
    def get_following_sibling(element):
        return element.find_element(By.XPATH, "following-sibling::*[1]")

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
        self._driver.get(self.live_server_url + url)

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


# end of file
