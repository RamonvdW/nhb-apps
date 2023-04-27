# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms
from django.urls import resolve, Resolver404


class LoginForm(forms.Form):
    """
        Dit formulier wordt gebruikt om in te loggen
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')   # voorkom de dubbele punt
        super().__init__(*args, **kwargs)

    login_naam = forms.CharField(
                        label='Inlog naam (NHB nummer of e-mailadres)',
                        max_length=50,
                        required=False,
                        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'}))

    wachtwoord = forms.CharField(
                        max_length=50,
                        required=False,
                        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))

    aangemeld_blijven = forms.BooleanField(
                        label='Aangemeld blijven',
                        initial=False,
                        required=False)     # avoids form validation failure when not checked

    next = forms.CharField(
                        required=False,
                        widget=forms.HiddenInput())

    def is_valid(self):
        """
            Deze methode wordt gebruikt door views::login om de input
            velden te controleren als op de Log In button gedrukt is.

            Bij problemen met de input wordt een error toegevoegd
            die door login.dtl in het formulier getoond worden aan de gebruiker.
        """
        valid = super(forms.Form, self).is_valid()
        if valid:
            login_naam = self.cleaned_data.get("login_naam")
            wachtwoord = self.cleaned_data.get("wachtwoord")
            # print("cleaned_data: %s" % repr(self.cleaned_data))
            if login_naam == "" or wachtwoord == "":
                self.add_error(None, 'Niet alle velden zijn ingevuld')
                valid = False

            # 'next' is checked when used, not here

        return valid


class ZoekAccountForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor de Login-As functionaliteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Deel van naam of inlog:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': ''}))


class KiesAccountForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests de keuze te ontvangen
        van het verborgen formulier
    """
    selecteer = forms.IntegerField(required=False)


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

    def _validate_otp_code(self, valid):
        if valid:
            otp_code = self.cleaned_data.get('otp_code')
            try:
                code = int(otp_code)
                # prevent negative numbers
                if code < 0 or code > 999999:
                    raise ValueError()
            except ValueError:
                self.add_error(None, 'Voer de vereiste code in')
                valid = False
        return valid

    def _validate_next_url(self, valid):
        if valid:
            next_url = self.cleaned_data.get('next_url')
            if next_url:
                if next_url[-1] != '/':
                    next_url += '/'
                try:
                    resolve(next_url)
                except Resolver404:
                    # cancel this invalid URL
                    valid = False
        return valid

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        valid = self._validate_otp_code(valid)
        valid = self._validate_next_url(valid)

        if not valid:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')
        return valid


# end of file
