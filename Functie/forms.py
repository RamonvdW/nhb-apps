# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ZoekBeheerdersForm(forms.Form):
    """ definitie van het formulier waarmee de beheerder een zoekterm in kan voeren
        om te zoeken naar een NHB lid.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoeken naar:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))


class WijzigBeheerdersForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests wijzigingen te ontvangen
        van verborgen formulieren
    """
    add = forms.IntegerField(required=False)
    drop = forms.IntegerField(required=False)


class AccepteerVHPGForm(forms.Form):
    """ Dit formulier wordt gebruikt bij de acceptatie van de verklaring hanteren persoonsgegevens (VHPG)
    """

    my_errors = {
        'required': 'verplicht',
    }

    accepteert = forms.BooleanField(
                        label='Ik accepteer bovenstaande',
                        initial=False,
                        required=True,     # checkbox must be crossed in
                        error_messages=my_errors)


class WijzigEmailForm(forms.Form):
    """ Dit formulier wordt gebruikt om het e-mailadres van een rol aan te passen """

    email = forms.EmailField(
                    label='Nieuwe e-mailadres',
                    widget=forms.TextInput(attrs={'autofocus': True}))


# end of file
