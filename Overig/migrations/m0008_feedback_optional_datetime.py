# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Overig', 'm0007_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='sitefeedback',
            name='toegevoegd_op',
            field=models.DateTimeField(null=True),
        ),
    ]

# end of file
