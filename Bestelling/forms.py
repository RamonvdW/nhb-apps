# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ZoekBestellingForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor Bestel Activiteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoektekst in kan voeren
    zoekterm = forms.CharField(
                        label='Nummer of deel van naam',
                        widget=forms.TextInput(attrs={'autofocus': True}),
                        max_length=50,
                        required=False)     # allow absence

    webwinkel = forms.BooleanField(
                        label='Toon webwinkel',
                        required=False)     # allow absence

    wedstrijden = forms.BooleanField(
                        label='Toon wedstrijden',
                        required=False)     # allow absence

    evenementen = forms.BooleanField(
                        label='Toon evenementen',
                        required=False)     # allow absence

    gratis = forms.BooleanField(
                        label='Toon gratis producten',
                        required=False)     # allow absence


# end of file
