# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


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
                        widget=forms.TextInput(attrs={'autofocus': True}))

    wachtwoord = forms.CharField(
                        max_length=50,
                        required=False,
                        widget=forms.PasswordInput())

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

        return valid


class ZoekAccountForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor de Login-As functionaliteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': ''}))


class KiesAccountForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests de keuze te ontvangen
        van het verborgen formulier
    """
    selecteer = forms.IntegerField(required=False)



# end of file
