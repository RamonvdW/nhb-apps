# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Mailer', 'm0004_html_body'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='mailqueue',
            name='template_used',
            field=models.CharField(default='', max_length=100),
        ),
    ]

# end of file
