# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Bestelling', 'm0014_rename'),
        ('Spelden', 'm0009_aanvraag_fixes'),
        ('Wedstrijden', 'm0067_kwalificatiescore_uitslag'),
    ]

    # migratie functies
    operations = [
        migrations.DeleteModel(
            name='SpeldBijlage',
        ),

        migrations.RenameField(
            model_name='speldaanvraag',
            old_name='soort_speld',
            new_name='speld',
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='last_email_reminder',
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='leeftijdsklasse',
        ),
        migrations.AddField(
            model_name='speldaanvraag',
            name='bestelling_regel',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.CASCADE,
                                    to='Bestelling.bestellingregel'),
        ),
        migrations.AddField(
            model_name='speldaanvraag',
            name='informatie_wedstrijd',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='speldaanvraag',
            name='score',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='speldaanvraag',
            name='wedstrijd_geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw')], default='M', max_length=1),
        ),
        migrations.AlterField(
            model_name='speldaanvraag',
            name='wedstrijd',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Wedstrijden.wedstrijd'),
        ),
        migrations.RemoveField(
            model_name='speldaanvraag',
            name='boog_type',
        ),
        migrations.AddField(
            model_name='speldaanvraag',
            name='boog',
            field=models.CharField(choices=[('R', 'Recurve'), ('C', 'Compound'), ('BB', 'Barebow')], default='R',
                                   max_length=2),
        ),
        migrations.AlterField(
            model_name='speldaanvraag',
            name='door_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL,
                                    to='Account.account'),
        ),

        migrations.AddField(
            model_name='speldaanvraagprep',
            name='datum_wedstrijd',
            field=models.DateField(default='2000-01-01'),
        ),
        migrations.AddField(
            model_name='speldaanvraagprep',
            name='informatie_wedstrijd',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='speldaanvraagprep',
            name='wedstrijd',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijd'),
        ),
        migrations.AlterField(
            model_name='speldaanvraagprep',
            name='voor_sporter',
            field=models.ForeignKey(on_delete=models.deletion.CASCADE, to='Sporter.sporter'),
        ),
    ]

# end of file
