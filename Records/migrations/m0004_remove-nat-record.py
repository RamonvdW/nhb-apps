# -*- coding: utf-8 -*-

#  Copyright (c) 2019 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


class Migration(migrations.Migration):
    """ Migratie class voor dit deel van de applicatie """

    dependencies = [
        ('Records', 'm0003_para-klasse'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='indivrecord',
            name='is_national_record',
        ),
    ]

# end of file
