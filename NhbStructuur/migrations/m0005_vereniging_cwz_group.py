# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        ('NhbStructuur', 'm0004_verwijder-postcode-huisnummer'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhbvereniging',
            name='cwz_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.PROTECT, to='auth.Group'),
        ),
    ]

# end of file
