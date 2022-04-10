# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def maak_boogtypen_ifaa(apps, _):
    """ Voeg de boogtypen voor IFAA toe.
    """

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    ifaa = 'F'  # International Field Archery Association

    # maak de standaard boogtypen aan
    # pk=1..6 = WA
    bulk = [boogtype_klas(pk=7, organisatie=ifaa, afkorting='BBR', volgorde='A', beschrijving='Barebow Recurve'),
            boogtype_klas(pk=8, organisatie=ifaa, afkorting='BBC', volgorde='B', beschrijving='Barebow Compound'),
            boogtype_klas(pk=9, organisatie=ifaa, afkorting='FSR', volgorde='F', beschrijving='Freestyle Limited Recurve'),
            boogtype_klas(pk=10, organisatie=ifaa, afkorting='FSC', volgorde='G', beschrijving='Freestyle Limited Compound'),
            boogtype_klas(pk=11, organisatie=ifaa, afkorting='FU',  volgorde='H', beschrijving='Freestyle Unlimited'),
            boogtype_klas(pk=12, organisatie=ifaa, afkorting='BHR', volgorde='K', beschrijving='Bowhunter Recurve'),
            boogtype_klas(pk=13, organisatie=ifaa, afkorting='BHC', volgorde='L', beschrijving='Bowhunter Compound'),
            boogtype_klas(pk=14, organisatie=ifaa, afkorting='BHU', volgorde='M', beschrijving='Bowhunter Unlimited'),
            boogtype_klas(pk=15, organisatie=ifaa, afkorting='BHL', volgorde='N', beschrijving='Bowhunter Limited'),
            boogtype_klas(pk=16, organisatie=ifaa, afkorting='ITR', volgorde='P', beschrijving='Traditional Recurve Bow'),
            boogtype_klas(pk=17, organisatie=ifaa, afkorting='ILB', volgorde='R', beschrijving='Longbow'),
            boogtype_klas(pk=18, organisatie=ifaa, afkorting='IHB', volgorde='T', beschrijving='Historical Bow')]

    boogtype_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0033_buiten_gebruik'),
    ]

    # migratie functies
    operations = [
        migrations.RunPython(maak_boogtypen_ifaa),
    ]

# end of file