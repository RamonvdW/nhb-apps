# -*- coding: utf-8 -*-

#  Copyright (c) 2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from TestHelpers import browser_helper as bh
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


class TestBrowserBondspasOphalen(bh.BrowserTestCase):

    url_otp_controle = '/account/otp-controle/'

    def test_otp_controle(self):

        # uitloggen (voor het geval we ingelogd waren en OTP controle al gedaan was)
        self.do_logout()

        # inloggen (zonder OTP controle)
        self.do_login()

        # zorg dat we ingelogd zijn
        self.do_login()     # navigeert al naar OTP controle check

        # OTP controle dialoog oproepen
        self.do_navigate_to(self.url_otp_controle, max_tries=1, may_fail=True)
        self.assertEqual(self._driver.title, 'Controle tweede factor MijnHandboogsport')

        # check dat er geen inlaad fouten waren
        self.assert_no_console_log()

        code = self._driver.find_element(By.ID, 'id_otp_code')

        self._driver.find_element(By.ID, 'otp1').send_keys('99a9')
        self.assertEqual(code.get_attribute("value"), '999')

        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)
        self.assertEqual(code.get_attribute("value"), '99')

        self._driver.find_element(By.ID, 'otp5').send_keys('888')
        self.assertEqual(code.get_attribute("value"), '99888')

        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)

        # backspace on empty input
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.BACKSPACE)

        # paste in a number
        script = "const cl = new DataTransfer();"
        script += "cl.setData('text/plain', '111111');"
        script += "const ce = new ClipboardEvent('paste', {clipboardData: cl});"
        script += "window.dispatchEvent(ce);"
        self._driver.execute_script(script)

        # check dat er geen fouten waren
        self.assert_no_console_log()


# end of file
