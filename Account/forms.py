# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class LoginForm(forms.Form):
    """
        Dit formulier wordt gebruikt om in te loggen
    """
    login_naam = forms.CharField(
                        label='Inlog naam',
                        max_length=50,
                        required=False,
                        widget=forms.TextInput(attrs={'autofocus': True}))
    wachtwoord = forms.CharField(
                        max_length=50,
                        required=False,
                        widget=forms.PasswordInput())

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
        return valid


class RegistreerForm(forms.Form):
    """
        Dit formulier wordt gebruikt om een nieuw account aan te maken
        met een NHB nummer.
    """
    nhb_nummer = forms.CharField(
                        label='NHB nummer',
                        min_length=6,
                        max_length=6,
                        required=True,
                        widget=forms.TextInput(attrs={'autofocus': True}))

    email = forms.EmailField(
                        label='E-mail adres zoals bekend bij de NHB',
                        required=True)

    nieuw_wachtwoord = forms.CharField(
                        label='Kies een wachtwoord',
                        max_length=50,
                        required=False,
                        widget=forms.PasswordInput())

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            nhb_nummer = self.cleaned_data.get('nhb_nummer')
            email = self.cleaned_data.get('email')
            nieuw_wachtwoord = self.cleaned_data.get('nieuw_wachtwoord')
            if nhb_nummer == "" or email == "" or nieuw_wachtwoord == "":
                self.add_error(None, 'Niet alle velden zijn ingevuld')
                valid = False
        else:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')

        return valid


class OTPControleForm(forms.Form):
    """ Dit formulier wordt gebruikt om de OTP code te ontvangen van de gebruiker """

    otp_code = forms.CharField(
                        label='Code',
                        min_length=6,
                        max_length=6,
                        required=True,
                        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'off'}))

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            otp_code = self.cleaned_data.get('otp_code')
            if otp_code == "":
                self.add_error(None, 'Voer de vereiste code in')
                valid = False
            else:
                try:
                    code = int(otp_code)
                except ValueError:
                    self.add_error(None, 'Voer de vereist code in')
                    valid = False
        else:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')

        return valid


# end of file
