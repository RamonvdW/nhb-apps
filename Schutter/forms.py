# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms

from Account.models import account_test_wachtwoord_sterkte


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
                valid, errmsg = account_test_wachtwoord_sterkte(nieuw_wachtwoord, nhb_nummer)
                if not valid:
                    self.add_error(None, errmsg)
        else:
            self.add_error(None, 'De gegevens worden niet geaccepteerd')

        return valid


class ScoreGeschiedenisForm(forms.Form):
    """ definitie van het formulier waarmee de een zoekterm in kan voeren
        om te zoeken naar een account. Wordt gebruikt voor de Login-As functionaliteit.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='NHB nummer:',
                    max_length=50,
                    required=False,
                    widget=forms.TextInput(attrs={'autofocus': ''}))

# end of file
