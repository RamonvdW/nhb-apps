# -*- coding: utf-8 -*-

#  Copyright (c) 2023-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from Competitie.models import Competitie


class SeizoenCache(object):

    """ Helper voor conversie van een urlconf parameter voor de competities

        comp_pk_of_seizoen --> kan comp_pk zijn zoals '7' of een seizoen url zoals 'indoor-2022-2023'
    """

    def __init__(self):
        # cache zodat we niet steeds naar de database hoeven
        self._seizoen2comp_pk = dict()

    def _fill_cache(self):
        for comp in Competitie.objects.all():
            seizoen = comp.maak_seizoen_url()
            self._seizoen2comp_pk[seizoen] = comp.pk
            self._seizoen2comp_pk[comp.pk] = comp.pk
            self._seizoen2comp_pk[str(comp.pk)] = comp.pk
        # for

    def get_comp_pk(self, comp_pk_of_seizoen):

        # indoor-2020-2021         = 16
        # 25m1pijl-2020-2021       = 18
        comp_pk_of_seizoen = str(comp_pk_of_seizoen)[:18].lower()       # afkappen voor de veiligheid

        try:
            # werkt op comp_pk en seizoen string ('indoor-2022-2023')
            return self._seizoen2comp_pk[comp_pk_of_seizoen]
        except KeyError:
            pass

        # we zouden hier een sanity-check kunnen doen zodat we de database niet onnodig benaderen
        # comp_pk_of_seizoen moet een integer zijn of
        #                    beginnen met 'indoor-' of '25m1pijl-' en minstens 2 streepjes bevatten

        is_ok = False
        if comp_pk_of_seizoen.startswith('indoor-') or comp_pk_of_seizoen.startswith('25m1pijl-'):
            is_ok = True
        else:
            try:
                _ = int(comp_pk_of_seizoen[:6])       # afkappen voor de veiligheid
                is_ok = True
            except ValueError:
                pass

        if is_ok:
            # reload the cache (nodig voor vers aangemaakte competities)
            self._fill_cache()

            # nog een keer
            try:
                return self._seizoen2comp_pk[comp_pk_of_seizoen]
            except KeyError:
                pass

        return 999999

    def reset(self):
        # used by autotest suite because of regular switching to new Competitie records
        self._seizoen2comp_pk = dict()


seizoen_cache = SeizoenCache()


def get_comp_pk(comp_pk_or_seizoen: str) -> int:
    """ converteer een urlconf 'comp_pk' naar een pk getal voor een Competitie
        vertaalt ook een seizoen naar comp_pk
    """
    return seizoen_cache.get_comp_pk(comp_pk_or_seizoen)


# end of file
