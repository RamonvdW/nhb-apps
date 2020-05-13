# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models


def zet_accounts(apps, schema_editor):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    account_klas = apps.get_model('Account', 'Account')
    functie_klas = apps.get_model('Functie', 'Functie')

    # doorloop 1x alle Accounts en daarna 1x alle Functies
    functie_accounts = dict()   # [functie_pk] = [account, account]

    for obj in account_klas.objects.all():              # pragma: no cover
        functie_pks = obj.temp_functies.split(',')
        for functie_pk in functie_pks:
            try:
                functie_accounts[functie_pk].append(obj)
            except KeyError:
                functie_accounts[functie_pk] = list()
                functie_accounts[functie_pk].append(obj)
        # for
    # for

    for obj in functie_klas.objects.all():
        try:
            accounts = functie_accounts[str(obj.pk)]
        except KeyError:
            # geen accounts gekoppeld aan deze functie
            pass
        else:
            for account in accounts:                    # pragma: no cover
                obj.accounts.add(account)
            # for
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('Functie', 'm0004_delete_cwz_with_nhbver'),
        ('Account', 'm0010_migrate_functie_nhblid_part2'),  # verwijdert Account.functies
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='functie',
            name='accounts',
            field=models.ManyToManyField(to='Account.Account'),
        ),
        migrations.RunPython(zet_accounts),
    ]

# end of file
