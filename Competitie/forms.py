# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class FavorieteBestuurdersForm(forms.Form):
    """ definitie van het formulier waarmee de bestuurder een zoekterm in kan voeren
        om te zoeken naar een NHB lid.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))


class WijzigFavorieteBestuurdersForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests wijzigingen te ontvangen
        van verborgen formulieren
    """
    add_nhb_nr = forms.CharField(max_length=6, required=False)
    drop_nhb_nr = forms.CharField(max_length=6, required=False)


# end of file
