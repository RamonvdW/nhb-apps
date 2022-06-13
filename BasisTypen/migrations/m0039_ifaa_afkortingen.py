# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


IFAA_LEEFTIJD_AFKORTING = {
    'SEM': 'SM',
    'SEV': 'SF',
    'VEM': 'VM',
    'VEV': 'VF',
    'VWH': 'AM',
    'VWV': 'AF',
    'JVH': 'YAM',
    'JVV': 'YAF',
    'JUH': 'JM',
    'JUV': 'JF',
    'WEH': 'CM',
    'WEV': 'CF',
}

IFAA_BOOG_AFKORTING = {
    'BBR': 'BB-R',
    'BBC': 'BB-C',
    'FSR': 'FS-R',
    'FSC': 'FS-C',
    'FU': 'FU',
    'BHR': 'BH-R',
    'BHC': 'BH-C',
    'BHU': 'BU',
    'BHL': 'BL',
    'ITR': 'TR',
    'ILB': 'LB',
    'IHB': 'HB',
}


def maak_kalenderwedstrijdklassen_ifaa_afkortingen(apps, _):
    """ Voeg de officiele afkortingen toe aan de IFAA kalender wedstrijdklassen """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    kalenderwedstrijdklasse_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')
    ifaa = 'F'  # International Field Archery Association

    for klasse in (kalenderwedstrijdklasse_klas
                   .objects
                   .filter(organisatie=ifaa)
                   .select_related('boogtype',
                                   'leeftijdsklasse')):      # pragma: no cover

        klasse.afkorting = IFAA_LEEFTIJD_AFKORTING[klasse.leeftijdsklasse.afkorting]
        klasse.afkorting += IFAA_BOOG_AFKORTING[klasse.boogtype.afkorting]

        klasse.save(update_fields=['afkorting'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0038_ifaa_wedstrijdklassen'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='leeftijdsklasse',
            name='wedstrijd_geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('A', 'Genderneutraal')], max_length=1),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdklasse',
            name='afkorting',
            field=models.CharField(default='?', max_length=10),
        ),
        migrations.RunPython(maak_kalenderwedstrijdklassen_ifaa_afkortingen),
    ]

# end of file
