# -*- coding: utf-8 -*-

#  Copyright (c) 2022-2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestel', 'm0022_fix_auto_date'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='bestelling',
            name='status',
            field=models.CharField(choices=[('N', 'Nieuw'), ('B', 'Betaling actief'), ('A', 'Afgerond'),
                                            ('F', 'Mislukt'), ('G', 'Geannuleerd')], default='N', max_length=1),
        ),
    ]

# end of file
