# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.


# alles in kleine letter
VERBODEN_WOORDEN_IN_WACHTWOORD = (
    'password',
    'wachtwoord',
    'geheim',
    'handboog',
    # keyboard walks
    '12345',
    '23456',
    '34567',
    '45678',
    '56789',
    '67890',
    'qwert',
    'werty',
    'ertyu',
    'rtyui',
    'tyuio',
    'yuiop',
    'asdfg',
    'sdfgh',
    'dfghj',
    'fghjk',
    'ghjkl',
    'zxcvb',
    'xcvbn',
    'cvbnm'
)


def account_test_wachtwoord_sterkte(wachtwoord, verboden_str):
    """ Controleer de sterkte van het opgegeven wachtwoord
        Retourneert: True,  None                als het wachtwoord goed genoeg is
                     False, "een error message" als het wachtwoord niet goed genoeg is
    """

    # we willen voorkomen dat mensen eenvoudig te RADEN wachtwoorden kiezen
    # of wachtwoorden die eenvoudig AF TE KIJKEN zijn

    # controleer de minimale length
    if len(wachtwoord) < 9:
        return False, "Wachtwoord moet minimaal 9 tekens lang zijn"

    # verboden_str is de inlog naam
    if verboden_str in wachtwoord:
        return False, "Wachtwoord bevat een verboden reeks"

    # entropie van elk teken is gelijk, dus het verminderen van de zoekruimte is niet verstandig
    # dus NIET: controleer op alleen cijfers

    lower_wachtwoord = wachtwoord.lower()

    # tel het aantal unieke tekens dat gebruikt is
    # (voorkomt wachtwoorden zoals jajajajajaja of xxxxxxxxxx)
    if len(set(lower_wachtwoord)) < 5:
        return False, "Wachtwoord bevat te veel gelijke tekens"

    # detecteer herkenbare woorden en keyboard walks
    for verboden_woord in VERBODEN_WOORDEN_IN_WACHTWOORD:
        if verboden_woord in lower_wachtwoord:
            return False, "Wachtwoord is niet sterk genoeg"

    return True, None

# end of file
