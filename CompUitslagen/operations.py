# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.urls import reverse
from Overig.helpers import make_valid_hashtag


def maak_url_uitslag_bk_indiv(seizoen_url: str, boog_type_url: str, klasse_str: str):
    url = reverse('CompUitslagen:uitslagen-bk-indiv',
                  kwargs={'comp_pk_of_seizoen': seizoen_url,
                          'comp_boog': boog_type_url})
    url += '#' + make_valid_hashtag(klasse_str)
    return url


def maak_url_uitslag_bk_teams(seizoen_url: str, team_type_url: str, klasse_str: str):
    url = reverse('CompUitslagen:uitslagen-bk-teams',
                  kwargs={'comp_pk_of_seizoen': seizoen_url,
                          'team_type': team_type_url})
    url += '#' + make_valid_hashtag(klasse_str)
    return url


def maak_url_uitslag_rk_indiv(seizoen_url: str, rayon_nr: int, boog_type_url: str, klasse_str: str):
    url = reverse('CompUitslagen:uitslagen-rk-indiv-n',
                  kwargs={'comp_pk_of_seizoen': seizoen_url,
                          'rayon_nr': rayon_nr,
                          'comp_boog': boog_type_url})
    url += '#' + make_valid_hashtag(klasse_str)
    return url


def maak_url_uitslag_rk_teams(seizoen_url: str, rayon_nr: int, team_type_url: str, klasse_str: str):
    url = reverse('CompUitslagen:uitslagen-rk-teams-n',
                  kwargs={'comp_pk_of_seizoen': seizoen_url,
                          'rayon_nr': rayon_nr,
                          'team_type': team_type_url})
    url += '#' + make_valid_hashtag(klasse_str)
    return url


# end of file
