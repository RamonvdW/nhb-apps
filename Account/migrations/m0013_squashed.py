# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.conf import settings
from django.db import migrations, models
import django.utils.timezone
import django.contrib.auth.models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('auth', '0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(help_text='Inlog naam', max_length=50, unique=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('vraag_nieuw_wachtwoord', models.BooleanField(default=False, help_text='Moet de gebruiker een nieuw wachtwoord opgeven bij volgende inlog?')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
                ('laatste_inlog_poging', models.DateTimeField(blank=True, null=True)),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_geblokkeerd_tot', models.DateTimeField(blank=True, help_text='Login niet mogelijk tot', null=True)),
                ('verkeerd_wachtwoord_teller', models.IntegerField(default=0, help_text='Aantal mislukte inlog pogingen op rij')),
                ('otp_code', models.CharField(blank=True, default='', help_text='OTP code', max_length=16)),
                ('otp_is_actief', models.BooleanField(default=False, help_text='Is OTP verificatie gelukt')),
                ('is_BB', models.BooleanField(default=False, help_text='Manager Competitiezaken')),
                ('is_Observer', models.BooleanField(default=False, help_text='Alleen observeren')),
            ],
            options={
                'verbose_name': 'Account',
                'verbose_name_plural': 'Accounts',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AccountEmail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_is_bevestigd', models.BooleanField(default=False)),
                ('bevestigde_email', models.EmailField(blank=True, max_length=254)),
                ('nieuwe_email', models.EmailField(blank=True, max_length=254)),
                ('optout_nieuwe_taak', models.BooleanField(default=False)),
                ('optout_herinnering_taken', models.BooleanField(default=False)),
                ('laatste_email_over_taken', models.DateTimeField(blank=True, null=True)),
                ('optout_functie_koppeling', models.BooleanField(default=False)),
                ('optout_reactie_klacht', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'AccountEmail',
                'verbose_name_plural': 'AccountEmails',
            },
        ),
        migrations.CreateModel(
            name='HanterenPersoonsgegevens',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acceptatie_datum', models.DateTimeField()),
                (
                'account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Hanteren Persoonsgegevens',
                'verbose_name_plural': 'Hanteren Persoonsgegevens',
            },
        ),
    ]

# end of file
