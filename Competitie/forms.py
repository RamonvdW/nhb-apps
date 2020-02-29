# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django import forms


class FavorieteBeheerdersForm(forms.Form):
    """ definitie van het formulier waarmee de beheerder een zoekterm in kan voeren
        om te zoeken naar een NHB lid.
    """

    # een simpel tekstveld waarin de gebruiker de zoek/filter tekst in kan voeren
    zoekterm = forms.CharField(
                    label='Zoek op:',
                    max_length=50,
                    required=False)


class WijzigFavorieteBeheerdersForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests wijzigingen te ontvangen
        van verborgen formulieren
    """
    add_favoriet = forms.IntegerField(required=False)
    drop_favoriet = forms.IntegerField(required=False)


class KoppelBeheerdersForm(forms.Form):
    """ Dit formulier wordt gebruikt om via POST requests wijzigingen te ontvangen
        van verborgen formulieren
    """

    def __init__(self, *args, **kwargs):
        fav_beheerders = kwargs.pop('fav_beheerders')       # super() is gevoelig voor onbekende velden
        super().__init__(*args, **kwargs)

        # maak extra velden aan voor verwachte beheerders
        # allemaal optioneel, want alleen de aangekruisde nummers komen terug
        for obj in fav_beheerders:
            self.fields['beheerder_%s' % obj.favoriet.pk] = forms.BooleanField(required=False)
        # for

    # standaard velden
    deelcomp_pk = forms.IntegerField()


# end of file
