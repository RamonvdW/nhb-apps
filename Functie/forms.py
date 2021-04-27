# -*- coding: utf-8 -*-

#  Copyright (c) 2020-2021 Ramon van der Winkel.
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


class OTPControleForm(forms.Form):
    """ Dit formulier wordt gebruikt om de OTP code te ontvangen van de gebruiker """

    otp_code = forms.CharField(
                        label='Code',
                        min_length=6,
                        max_length=6,
                        required=True,
                        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'off'}))

    next_url = forms.CharField(
                        required=False,
                        widget=forms.HiddenInput())

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            otp_code = self.cleaned_data.get('otp_code')
            try:
                code = int(otp_code)
            except ValueError:
                self.add_error(None, 'Voer de vereiste code in')
                valid = False
        else:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')

        return valid


class WijzigEmailForm(forms.Form):
    """ Dit formulier wordt gebruikt om het e-mailadres van een rol aan te passen """

    email = forms.EmailField()


# end of file
