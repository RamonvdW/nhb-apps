# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
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

    aangemeld_blijven = forms.BooleanField(
                        label='Aangemeld blijven',
                        initial=False,
                        required=False)     # avoids form validation failure when not checked

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


# alles in kleine letter
VERBODEN_WOORDEN_IN_WACHTWOORD = (
    'password',
    'wachtwoord',
    'geheim',
    'handboog',
    # keyboard walks
    '12345',
    '23456',
    '34567',
    '45678',
    '56789',
    '67890',
    'qwert',
    'werty',
    'ertyu',
    'rtyui',
    'tyuio',
    'yuiop',
    'asdfg',
    'sdfgh',
    'dfghj',
    'fghjk',
    'ghjkl',
    'zxcvb',
    'xcvbn',
    'cvbnm'
)

def test_wachtwoord_sterkte(wachtwoord, verboden_str):
    """ Controleer de sterkte van het opgegeven wachtwoord
        Retourneert: True,  None                als het wachtwoord goed genoeg is
                     False, "een error message" als het wachtwoord niet goed genoeg is
    """

    # controleer de minimale length
    if len(wachtwoord) < 9:
        return False, "Wachtwoord moet minimaal 9 tekens lang zijn"

    # controleer op alleen cijfers
    if wachtwoord.isdigit():
        return False, "Wachtwoord bevat alleen cijfers"

    if verboden_str in wachtwoord:
        return False, "Wachtwoord bevat een verboden reeks"

    lower_wachtwoord = wachtwoord.lower()

    # tel het aantal unieke tekens dat gebruikt is
    # (voorkomt wachtwoorden zoals jajajajajaja of xxxxxxxxxx)
    if len(set(lower_wachtwoord)) < 5:
        return False, "Wachtwoord bevat te veel gelijke tekens"

    # detecteer herkenbare woorden en keyboard walks
    for verboden_woord in VERBODEN_WOORDEN_IN_WACHTWOORD:
        if verboden_woord in lower_wachtwoord:
            return False, "Wachtwoord is niet sterk genoeg"

    return True, None


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
                valid, errmsg = test_wachtwoord_sterkte(nieuw_wachtwoord, nhb_nummer)
                if not valid:
                    self.add_error(None, errmsg)
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
            try:
                code = int(otp_code)
            except ValueError:
                self.add_error(None, 'Voer de vereiste code in')
                valid = False
        else:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')

        return valid


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




# end of file
