# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ScoreGeschiedenisForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een NHB nummer voor de Score Geschiedenis functionaliteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='NHB nummer:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': ''}))

# end of file
