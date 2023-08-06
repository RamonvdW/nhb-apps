# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def kopieer_email_instellingen(apps, _):
    """ kopieer informatie van AccountEmail in Account """

    email_klas = apps.get_model('Account', 'AccountEmail')

    for email in email_klas.objects.select_related('account').all():        # pragma: no cover
        account = email.account

        account.email_is_bevestigd = email.email_is_bevestigd
        account.bevestigde_email = email.bevestigde_email
        account.nieuwe_email = email.nieuwe_email
        account.optout_nieuwe_taak = email.optout_nieuwe_taak
        account.optout_herinnering_taken = email.optout_herinnering_taken
        account.laatste_email_over_taken = email.laatste_email_over_taken

        account.save(update_fields=['email_is_bevestigd', 'bevestigde_email', 'nieuwe_email',
                                    'optout_nieuwe_taak', 'optout_herinnering_taken','laatste_email_over_taken'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0023_squashed'),
        ('Overig', 'm0012_merge_accountemail_1'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='account',
            name='is_Observer',
        ),
        migrations.AddField(
            model_name='account',
            name='bevestigde_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='account',
            name='email_is_bevestigd',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='account',
            name='laatste_email_over_taken',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='nieuwe_email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='account',
            name='optout_herinnering_taken',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='account',
            name='optout_nieuwe_taak',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(kopieer_email_instellingen, reverse_code=migrations.RunPython.noop),
    ]

# end of file
