# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Score', 'm0003_scorehist_when'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='scorehist',
            name='datum',
        ),
    ]

# end of file
