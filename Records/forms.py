# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ZoekForm(forms.Form):
    """ definitie van het formulier waarmee de gebruiker een zoekterm in kan voeren
        voor de records (naam / nummer)
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))

# end of file
