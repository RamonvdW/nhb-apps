# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0013_admin_blank_fields'),
        ('BasisTypen', 'm0009_basistypen_2020'),
        ('Wedstrijden', 'm0002_wedstrijdenplan'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='wedstrijd',
            name='indiv_klassen',
            field=models.ManyToManyField(blank=True, to='BasisTypen.IndivWedstrijdklasse'),
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='team_klassen',
            field=models.ManyToManyField(blank=True, to='BasisTypen.TeamWedstrijdklasse'),
        ),
        migrations.AlterField(
            model_name='wedstrijdenplan',
            name='wedstrijden',
            field=models.ManyToManyField(blank=True, to='Wedstrijden.Wedstrijd'),
        ),
        migrations.AlterField(
            model_name='wedstrijdlocatie',
            name='verenigingen',
            field=models.ManyToManyField(blank=True, to='NhbStructuur.NhbVereniging'),
        ),
    ]

# end of file
