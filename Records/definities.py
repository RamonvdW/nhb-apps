# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from BasisTypen.definities import GESLACHT_MAN, GESLACHT_VROUW

DISCIPLINE = [('OD', 'Outdoor'),
              ('18', 'Indoor'),
              ('25', '25m 1pijl')]

GESLACHT = [(GESLACHT_MAN, 'Man'),
            (GESLACHT_VROUW, 'Vrouw')]

# IB is in 2022 hernoemd naar TR
MATERIAALKLASSEN = ('R', 'C', 'BB', 'LB', 'TR', 'IB')

MATERIAALKLASSE = [('R', 'Recurve'),
                   ('C', 'Compound'),
                   ('BB', 'Barebow'),
                   ('LB', 'Longbow'),
                   ('TR', 'Traditional'),
                   ('IB', 'Instinctive bow')]   # IB = legacy

LEEFTIJDSCATEGORIE = [('M', 'Master'),     # ('m', '50+'),
                      ('S', 'Senior'),     # ('s', '21+'),
                      ('J', 'Junior'),     # ('j', 'Onder 21'),
                      ('C', 'Cadet'),      # ('c', 'Onder 18'),
                      ('U', 'Uniform (para)')]

# vertaling van velden naar urlconf elementen en terug
disc2str = {'OD': 'Outdoor',
            '18': 'Indoor',
            '25': '25m 1pijl'}

gesl2str = {'M': 'Heren',
            'V': 'Dames'}

# er zijn nooit IB records geregistreerd, dus we tonen die gewoon niet meer
makl2str = {'R': 'Recurve',
            'C': 'Compound',
            'BB': 'Barebow',
            # 'IB': 'Instinctive bow',
            'TR': 'Traditional',
            'LB': 'Longbow'}

# TODO: oude benaming verwijderen
lcat2str = {'M': '50+ / Masters',
            'S': '21+ / Senioren',
            'J': 'Onder 21 / Junioren',
            'C': 'Onder 18 / Cadetten',
            'U': 'Gecombineerd (bij para)'}     # alleen voor Outdoor

disc2url = {'OD': 'outdoor',
            '18': 'indoor',
            '25': '25m1pijl'}

gesl2url = {'M': 'heren',
            'V': 'dames'}

lcat2short = {'M': '50+',
              'S': '21+',
              'J': 'Onder 21',
              'C': 'Onder 18',
              'U': 'Gecombineerd (bij para)'}     # alleen voor Outdoor

verb2str = {True: 'Ja',
            False: 'Nee'}

makl2url = {'R': 'recurve',
            'C': 'compound',
            'BB': 'barebow',
            'TR': 'traditional',
            'LB': 'longbow'}

lcat2url = {'M': '50plus',
            'S': '21plus',
            'J': 'onder21',
            'C': 'onder18',
            'U': 'gecombineerd'}

verb2url = {True: 'ja',
            False: 'nee'}

# let op: in sync houden met settings.RECORDS_TOEGESTANE_PARA_KLASSEN
para2url = {'Open': 'open',
            'Staand': 'staand',
            'W1': 'W1',
            'W2': 'W2',
            'VI1': 'VI1',
            'VI2/3': 'VI2-3',
            '': 'nvt'}

url2disc = {v: k for k, v in disc2url.items()}
url2gesl = {v: k for k, v in gesl2url.items()}
url2makl = {v: k for k, v in makl2url.items()}
url2lcat = {v: k for k, v in lcat2url.items()}
url2verb = {v: k for k, v in verb2url.items()}
url2para = {v: k for k, v in para2url.items()}


# end of file
