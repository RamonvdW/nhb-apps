# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ZoekBeheerdersForm(forms.Form):
    """ definitie van het formulier waarmee de beheerder een zoekterm in kan voeren
        om te zoeken naar een NHB lid.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False)

class WijzigBeheerdersForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests wijzigingen te ontvangen
        van verborgen formulieren
    """
    add = forms.IntegerField(required=False)
    drop = forms.IntegerField(required=False)


class SelecteerSchutterForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests de keuze te ontvangen
        van het verborgen formulier
    """
    selecteer = forms.IntegerField(required=False)


# end of file
