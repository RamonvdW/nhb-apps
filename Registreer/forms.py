# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2025 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms
from Account.operations import account_test_wachtwoord_sterkte
from Mailer.operations import mailer_email_is_valide


def scrub_input_name(name):
    """ Remove garbage from form parameter that is supposed to contain a name.
        We allow a few special characters (UTF-8) but input that looks like HTML is not allowed.

        Used for: first name, last name, club name, city name, federation name
    """

    # remove characters typically not found in name
    for char in '<>#/()*&^%$@!=+_{}[]:;"\\|<>.?~`\'':        # Let op: cijfers zijn toegestaan voor naam vereniging
        name = name.replace(char, '')
    # for

    name = name.strip()     # remove spaces

    return name


class RegistreerNormaalForm(forms.Form):
    """
        Dit formulier wordt gebruikt om een nieuw account aan te maken
        met een bondsnummer.
    """
    lid_nr = forms.CharField(
                        label='Bondsnummer',
                        min_length=6,
                        max_length=6,
                        required=True,
                        widget=forms.TextInput(attrs={'autofocus': True}))

    email = forms.EmailField(
                        label='E-mail adres zoals bekend bij de bond',
                        required=True)

    nieuw_wachtwoord = forms.CharField(
                        label='Kies een wachtwoord',
                        max_length=50,
                        required=False,
                        widget=forms.PasswordInput())

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if valid:
            lid_nr = self.cleaned_data.get('lid_nr')
            email = self.cleaned_data.get('email')
            nieuw_wachtwoord = self.cleaned_data.get('nieuw_wachtwoord')

            if lid_nr == "" or email == "" or nieuw_wachtwoord == "":
                self.add_error(None, 'niet alle velden zijn ingevuld')
                valid = False
            else:
                valid, errmsg = account_test_wachtwoord_sterkte(nieuw_wachtwoord, lid_nr)
                if not valid:
                    self.add_error(None, errmsg)
        else:
            self.add_error(None, 'de gegevens worden niet geaccepteerd')

        return valid


class RegistreerGastForm(forms.Form):
    """
        Dit formulier wordt gebruikt om een gast-account aan te maken.
    """
    voornaam = forms.CharField(
                        label='Voornaam',
                        max_length=50,
                        required=True,
                        widget=forms.TextInput(attrs={'autofocus': True}))

    achternaam = forms.CharField(
                        label='Achternaam',
                        max_length=100,
                        required=True)

    email = forms.EmailField(
                        label='E-mail adres',
                        required=True)

    def clean_voornaam(self):
        out = scrub_input_name(self.cleaned_data['voornaam'])
        return out

    def clean_achternaam(self):
        out = scrub_input_name(self.cleaned_data['achternaam'])
        return out

    def clean_email(self):
        email = self.cleaned_data['email']
        # standaard EmailValidator checkt al heel wat, maar laat bijvoorbeeld x@localhost door
        if not mailer_email_is_valide(email):
            self.add_error('email', 'voer een geldig e-mailadres in')       # wordt nooit getoond
        return email

    def is_valid(self):
        valid = super(forms.Form, self).is_valid()
        if not valid:
            # None, want we tonen in de template alleen niet-field-specific errors
            self.add_error(None, 'de gegevens worden niet geaccepteerd')
        return valid


# end of file
