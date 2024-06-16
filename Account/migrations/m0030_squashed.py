# -*- coding: utf-8 -*-

#  Copyright (c) 2019-2024 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # dit is de eerste
    initial = True

    # volgorde afdwingen
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('sessions', '0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff',
                    models.BooleanField(
                        default=False,
                        help_text='Designates whether the user can log into this admin site.',
                        verbose_name='staff status')),
                ('is_active',
                    models.BooleanField(
                        default=True,
                        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                        verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('username', models.CharField(help_text='Inlog naam', max_length=50, unique=True)),
                ('unaccented_naam', models.CharField(blank=True, default='', max_length=200)),
                ('vraag_nieuw_wachtwoord', models.BooleanField(default=False, help_text='Moet de gebruiker een nieuw wachtwoord opgeven bij volgende inlog?')),
                ('laatste_inlog_poging', models.DateTimeField(blank=True, null=True)),
                ('verkeerd_wachtwoord_teller', models.IntegerField(default=0, help_text='Aantal mislukte inlog pogingen op rij')),
                ('is_geblokkeerd_tot', models.DateTimeField(blank=True, help_text='Login niet mogelijk tot', null=True)),
                ('is_BB', models.BooleanField(default=False, help_text='Manager MH')),
                ('otp_code', models.CharField(blank=True, default='', help_text='OTP code', max_length=32)),
                ('otp_is_actief', models.BooleanField(default=False, help_text='Is OTP verificatie gelukt')),
                ('groups',
                    models.ManyToManyField(
                        blank=True,
                        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                        related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.',
                                                            related_name='user_set', related_query_name='user',
                                                            to='auth.permission', verbose_name='user permissions')),
                ('otp_controle_gelukt_op', models.DateTimeField(blank=True, null=True)),
                ('bevestigde_email', models.EmailField(blank=True, max_length=254)),
                ('email_is_bevestigd', models.BooleanField(default=False)),
                ('laatste_email_over_taken', models.DateTimeField(blank=True, null=True)),
                ('nieuwe_email', models.EmailField(blank=True, max_length=254)),
                ('optout_herinnering_taken', models.BooleanField(default=False)),
                ('optout_nieuwe_taak', models.BooleanField(default=False)),
                ('is_gast', models.BooleanField(default=False)),
                ('scheids', models.CharField(blank=True, choices=[('N', 'Niet'), ('B', 'Bondsscheidsrechter'),
                                                                  ('V', 'Verenigingsscheidsrechter'),
                                                                  ('I', 'Internationaal Scheidsrechter')],
                                             default='N', max_length=2)),
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
            name='AccountSessions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              to='Account.account')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sessions.session')),
            ],
        ),
        migrations.CreateModel(
            name='AccountVerzoekenTeller',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uur_nummer', models.PositiveBigIntegerField(default=0)),
                ('teller', models.PositiveIntegerField(default=0)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              to='Account.account')),
            ],
        ),
    ]

# end of file
