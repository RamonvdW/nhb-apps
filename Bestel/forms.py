# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
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
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))

    webwinkel = forms.BooleanField(
                        label='Toon webwinkel',
                        initial=True,
                        required=False)     # avoids form validation failure when not checked

    wedstrijden = forms.BooleanField(
                        label='Toon wedstrijden',
                        initial=True,
                        required=False)     # avoids form validation failure when not checked


# end of file
