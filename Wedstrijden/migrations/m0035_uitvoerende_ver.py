# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0030_bondsbureau'),
        ('Wedstrijden', 'm0034_verkoopvoorwaarden'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijd',
            name='uitvoerende_vereniging',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, related_name='uitvoerend', to='NhbStructuur.nhbvereniging'),
        ),
    ]

# end of file
