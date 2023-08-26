# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Wedstrijden', 'm0041_vereniging_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='wedstrijd',
            name='organiserende_vereniging',
        ),
        migrations.RenameField(
            model_name='wedstrijd',
            old_name='organiserende_vereniging_new',
            new_name='organiserende_vereniging',
        ),
        migrations.AlterField(
            model_name='wedstrijd',
            name='organiserende_vereniging',
            field=models.ForeignKey(on_delete=models.deletion.PROTECT, to='Vereniging.vereniging'),
        ),

        migrations.RemoveField(
            model_name='wedstrijd',
            name='uitvoerende_vereniging',
        ),
        migrations.RenameField(
            model_name='wedstrijd',
            old_name='uitvoerende_vereniging_new',
            new_name='uitvoerende_vereniging',
        ),

        migrations.RemoveField(
            model_name='wedstrijdkorting',
            name='uitgegeven_door',
        ),
        migrations.RenameField(
            model_name='wedstrijdkorting',
            old_name='uitgegeven_door_new',
            new_name='uitgegeven_door',
        ),

        migrations.RemoveField(
            model_name='wedstrijdlocatie',
            name='verenigingen',
        ),
        migrations.RenameField(
            model_name='wedstrijdlocatie',
            old_name='verenigingen_new',
            new_name='verenigingen',
        ),
    ]

# end of file
