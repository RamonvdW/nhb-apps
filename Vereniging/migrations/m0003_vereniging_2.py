# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Vereniging', 'm0002_vereniging_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='secretaris',
            name='vereniging',
        ),
        migrations.RenameField(
            model_name='secretaris',
            old_name='vereniging_new',
            new_name='vereniging',
        ),
        migrations.AlterField(
            model_name='secretaris',
            name='vereniging',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Vereniging.vereniging'),
        ),
    ]

# end of file