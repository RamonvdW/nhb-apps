# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
from django.contrib.sessions.backends.db import SessionStore
import django.db.models.deletion


def koppel_sessies(apps, _):
    # ga eenmalig door alle sessies heen en koppel ze aan de juiste gebruiker

    # haal de klassen op die van toepassing zijn op het moment van migratie
    account_klas = apps.get_model('Account', 'Account')
    session_klas = apps.get_model('sessions', 'session')
    accses_klas = apps.get_model('Account', 'AccountSessions')

    sessies = dict()    # [account.pk] = [sessie1, sessie2, ..]
    store = SessionStore()

    for obj in session_klas.objects.all():                      # pragma: no cover
        data = store.decode(obj.session_data)

        try:
            auth_user_id = int(data['_auth_user_id'])
        except KeyError:
            # niet ingelogd
            pass
        else:
            try:
                sessies[auth_user_id].append(obj)
            except KeyError:
                sessies[auth_user_id] = [obj]
    # for

    # maak nu alle AccountSession aan
    bulk = list()

    # alle accounts in 1x ophalen
    pks = sessies.keys()
    for account in account_klas.objects.filter(pk__in=pks):     # pragma: no cover
        for sessie in sessies[account.pk]:
            accses = accses_klas(account=account, session=sessie)
            bulk.append(accses)
            if len(bulk) > 250:
                accses_klas.objects.bulk_create(bulk)
                bulk = list()
        # for
    # for

    if len(bulk):                                               # pragma: no cover
        accses_klas.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('sessions', '0001_initial'),
        ('Account', 'm0016_delete_vhpg'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='AccountSessions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sessions.session')),
            ],
        ),
        migrations.RunPython(koppel_sessies),
    ]

# end of file
