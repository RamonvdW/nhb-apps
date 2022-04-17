# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Kalender', 'm0008_inschrijving'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='kalenderwedstrijdkortingscode',
            name='combi_basis_wedstrijd',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='combi_korting', to='Kalender.kalenderwedstrijd'),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdkortingscode',
            name='soort',
            field=models.CharField(choices=[('s', 'Sporter'), ('v', 'Vereniging'), ('c', 'Combi')], default='v', max_length=1),
        ),
    ]

# end of file
