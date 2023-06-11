# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    # volgorde afdwingen
    dependencies = [
        ('TijdelijkeCodes', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='tijdelijkecode',
            name='hoortbij_gast',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Registreer.gastregistratie'),
        ),
    ]

# end of file
