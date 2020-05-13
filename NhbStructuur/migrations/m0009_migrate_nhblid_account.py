# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def zet_nhblid_account(apps, schema_editor):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    account_klas = apps.get_model('Account', 'Account')
    nhblid_klas = apps.get_model('NhbStructuur', 'NhbLid')

    # er zijn minder Accounts dan NhbLid records, dus doorloop Account
    for obj in account_klas.objects.all():
        if obj.temp_nhb_nr > 0:                 # pragma: no cover
            # zoek het NhbLid record erbij
            lid = nhblid_klas.objects.get(pk=obj.temp_nhb_nr)
            lid.account = obj
            lid.save()
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('NhbStructuur', 'm0008_vereniging_plaats_email'),
        ('Account', 'm0010_migrate_functie_nhblid_part2'),      # verwijdert Account.nhblid
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='nhblid',
            name='account',
            field=models.ForeignKey(blank=True, null=True,
                                    on_delete=django.db.models.deletion.SET_NULL,
                                    to='Account.Account'),
                                    #to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(zet_nhblid_account),
    ]

# end of file
