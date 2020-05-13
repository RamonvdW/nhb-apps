# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class FilterForm(forms.Form):
    """ definitie van het formulier waarmee de gebruiker een filter in kan voeren
        voor de historische competitie data (naam / nummer)
        en waarmee de pagina's gekozen kunnen worden.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    filter = forms.CharField(
                    label='Zoek naar:',
                    max_length=50,
                    required=False)

    # gevraagde pagina nummer
    pg = forms.IntegerField(        # TODO: is deze nodig?
                    min_value=1, max_value=1000,
                    required=False,
                    widget=forms.HiddenInput())

    # optie om alle data te laten zien en de paginator te omzeilen
    all = forms.IntegerField(
                    required=False,
                    widget=forms.HiddenInput())

# end of file
