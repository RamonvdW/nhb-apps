# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms

from Account.operations.wachtwoord import account_test_wachtwoord_sterkte


class RegistreerForm(forms.Form):
    """
        Dit formulier wordt gebruikt om een nieuw account aan te maken
        met een bondsnummer.
    """
    nhb_nummer = forms.CharField(
                        label='Bondsnummer',
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

# end of file
