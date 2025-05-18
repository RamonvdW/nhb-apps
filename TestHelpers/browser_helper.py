# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

""" helpers for testing via de browser """

from selenium.webdriver import Chrome, ChromeOptions, DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time


port = 8000
url_root = 'http://localhost:' + str(port)


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


def get_console_log(driver) -> list[str]:
    logs = driver.get_log('browser')
    regels = list()
    for log in logs:
        msg = log['message']
        if msg not in regels:
            regels.append(msg)
    return regels


def find_element_by_id(driver, id_str):
    return driver.find_element(By.ID, id_str)


def find_element_by_name(driver, name_str):
    return driver.find_element(By.NAME, name_str)


def find_element_type_with_text(driver, elem_type, text_str):
    try:
        el = driver.find_element(By.XPATH, '//%s[text()="%s"]' % (elem_type, text_str))
    except NoSuchElementException:
        el = None
    return el


def find_tabel_filter_input(driver, tabel_id):
    try:
        el_table = driver.find_element(By.ID, tabel_id)
    except NoSuchElementException:
        el_input = None
    else:
        el_input = el_table.find_element(By.XPATH, '//input[@class="table-filter"]')
    return el_input


def get_following_sibling(element):
    return element.find_element(By.XPATH, "following-sibling::*[1]")


def wait_until_url_not(driver, url: str, timeout: float = 2.0):
    duration = 0.5
    curr_url = driver.current_url
    while curr_url == url and timeout > 0:
        time.sleep(duration)
        timeout -= duration
        duration *= 2
        curr_url = driver.current_url
    # while

# end of file
