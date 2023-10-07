# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Scheidsrechter', 'm0002_is_hoofd_sr'),
    ]

    # migratie functies
    operations = [
        migrations.AddConstraint(
            model_name='scheidsbeschikbaarheid',
            constraint=models.UniqueConstraint(fields=('scheids', 'wedstrijd', 'datum'), name='Een per scheidsrechter en wedstrijd dag'),
        ),
    ]

# end of file
