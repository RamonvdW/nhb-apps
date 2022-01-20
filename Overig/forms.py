# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms
from .models import SiteFeedback


class SiteFeedbackForm(forms.Form):
    """ definitie van het formulier waarmee de gebruiker
        feedback kan geven op de site.
    """
    gebruiker = forms.CharField(
                    max_length=50,
                    required=False,
                    widget=forms.HiddenInput)

    op_pagina = forms.CharField(
                    max_length=50,
                    required=False,
                    widget=forms.HiddenInput)

    bevinding = forms.ChoiceField(
                    choices=SiteFeedback.FEEDBACK,
                    label='Je mening over de website pagina',
                    widget=forms.RadioSelect)

    feedback = forms.CharField(
                    label='Bericht aan het ontwikkelteam:',
                    max_length=2500,
                    required=True,
                    widget=forms.Textarea(
                        attrs={'autofocus': True,
                               'placeholder': 'Tik hier je bericht',
                               'data-length': 2500,
                               'class': 'materialize-textarea'}))


class ZoekAccountForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor Account Activiteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))


# end of file
