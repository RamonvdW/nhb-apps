# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class WedstrijdLocatieForm(forms.Form):
    """ Dit formulier wordt gebruikt om de details van een wedstrijdlocatie te ontvangen
    """

    baan_type = forms.CharField(
                            max_length=1,
                            required=True)

    banen_18m = forms.IntegerField(
                            required=True,
                            min_value=0,
                            max_value=25)

    banen_25m = forms.IntegerField(
                            required=True,
                            min_value=0,
                            max_value=25)

    max_dt = forms.IntegerField(
                            required=True,
                            min_value=3,
                            max_value=4)

    notities = forms.CharField(
                            max_length=1024,
                            required=False)

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            if self.cleaned_data.get('baan_type', '?') not in ('X', 'O', 'H'):
                valid = False

        return valid


# end of file
