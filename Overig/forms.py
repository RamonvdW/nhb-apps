# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
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
                        attrs={'placeholder': 'Tik hier je bericht',
                               'data-length': 2500,
                               'class': 'materialize-textarea'}))

# end of file
