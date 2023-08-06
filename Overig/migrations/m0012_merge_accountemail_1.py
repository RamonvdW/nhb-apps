# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def overzetten_naar_account(apps, _):                           # pragma: no cover
    """ verhuis hoortbij_accountemail naar hoortbij_account """

    url_klas = apps.get_model('Overig', 'SiteTijdelijkeUrl')

    for url in (url_klas
                .objects
                .exclude(hoortbij_accountemail=None)
                .prefetch_related('hoortbij_accountemail',
                                  'hoortbij_accountemail__account')
                .all()):

        url.hoortbij_account = url.hoortbij_accountemail.account
        url.save(update_fields=['hoortbij_account'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('Overig', 'm0011_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='sitetijdelijkeurl',
            name='hoortbij_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE, to='Account.account'),
        ),
        migrations.RunPython(overzetten_naar_account, reverse_code=migrations.RunPython.noop),
    ]

# end of file
