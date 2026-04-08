# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.test import TestCase
from Privacy.operations import laad_privacyverklaring, get_verklaring_doc
from TestHelpers.e2ehelpers import E2EHelpers
from unittest.mock import patch

inhoud_1 = """Header

Dit wordt een paragraaf
*een lijst
**tweede lijst
**nog een tweede
=heading na lijst
*een lijst
**tweede lijst gevolgd door lege regel

paragraaf
=heading na paragraaf
*level 1
**level2
*terug op level 1
**level2
paragraaf na lijst
paragraaf met %link%linkje%www.test.not nog meer tekst
lege regels aan het einde

"""

expected_doc = [
    ('h1', 'Header'),
    ('br', ''),
    ('p', 'Dit wordt een paragraaf'),
    ('*+', ''),
    ('**+', 'een lijst'),
    ('*', 'tweede lijst'),
    ('*', 'nog een tweede'),
    ('**-', ''),
    ('*-', ''),
    ('h2', 'heading na lijst'),
    ('*+', ''),
    ('**+', 'een lijst'),
    ('*', 'tweede lijst gevolgd door lege regel'),
    ('**-', ''),
    ('*-', ''), ('br', ''),
    ('p', 'paragraaf'),
    ('h2', 'heading na paragraaf'),
    ('*+', ''),
    ('**+', 'level 1'),
    ('*', 'level2'),
    ('**-', ''),
    ('**+', 'terug op level 1'),
    ('*', 'level2'),
    ('**-', ''),
    ('*-', ''),
    ('p', 'paragraaf na lijst'),
    ('p1', 'paragraaf met '),
    ('a1', 'www.test.not'),
    ('a2', 'linkje'),
    ('p2', ' nog meer tekst'),
    ('p', 'paragraaf met %link%linkje%www.test.not nog meer tekst'),
    ('p', 'lege regels aan het einde')
]

class OpenMock:

    def __init__(self, inhoud):
        self._inhoud = inhoud

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def readlines(self):
        return self._inhoud.splitlines()


class TestPrivacyOperations(E2EHelpers, TestCase):

    """ tests voor de Privacy-applicatie, operations """

    def setUp(self):
        """ initialisatie van de test case """
        pass

    def test_laad(self):
        open_mock = OpenMock(inhoud_1)
        with patch('Privacy.operations.open', return_value=open_mock):
            laad_privacyverklaring('test.txt')

            doc = get_verklaring_doc()
            self.assertEqual(doc, expected_doc)


# end of file
