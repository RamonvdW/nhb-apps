# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class AccommodatieDetailsForm(forms.Form):
    """ Dit formulier wordt gebruikt om de details van een wedstrijdlocatie te ontvangen
    """

    baan_type = forms.CharField(
                            required=False,
                            max_length=1)

    banen_18m = forms.IntegerField(
                            required=False,
                            min_value=0,
                            max_value=25)

    banen_25m = forms.IntegerField(
                            required=False,
                            min_value=0,
                            max_value=25)

    max_sporters_18m = forms.IntegerField(
                            required=False,
                            min_value=0,
                            max_value=99)

    max_sporters_25m = forms.IntegerField(
                            required=False,
                            min_value=0,
                            max_value=99)

    notities = forms.CharField(
                            required=False,
                            max_length=1024)

    buiten_adres = forms.CharField(
                            required=False,
                            max_length=1024)

    buiten_banen = forms.IntegerField(
                            required=False,
                            min_value=1,
                            max_value=80)

    buiten_max_afstand = forms.IntegerField(
                            required=False,
                            min_value=30,
                            max_value=100)

    buiten_notities = forms.CharField(
                            required=False,
                            max_length=1024)

    disc_25m1p = forms.BooleanField(required=False)
    disc_outdoor = forms.BooleanField(required=False)
    disc_indoor = forms.BooleanField(required=False)
    disc_clout = forms.BooleanField(required=False)
    disc_veld = forms.BooleanField(required=False)
    disc_run = forms.BooleanField(required=False)
    disc_3d = forms.BooleanField(required=False)

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            if self.cleaned_data.get('baan_type', '?') not in ('X', 'O', 'H'):
                valid = False

        return valid


# end of file
