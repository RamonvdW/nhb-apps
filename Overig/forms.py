# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class ZoekAccountForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor Account Activiteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoektekst in kan voeren
    zoekterm = forms.CharField(
                    label='Bondsnummer of deel volledige naam:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': True}))

    def clean(self):
        super().clean()

        # ignore errors
        if 'zoekterm' in self._errors:
            del self._errors['zoekterm']

# end of file
