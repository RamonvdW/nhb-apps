# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def migreer_ag_velden(apps, _):
    """ aanvangsgemiddelde --> ag_voor_indiv, ag_voor_team
        is_handmatig_ag --> (n.v.t. voor indiv), ag_voor_team_mag_aangepast_worden
    """

    deelnemer_klas = apps.get_model('Competitie', 'RegioCompetitieSchutterBoog')

    for obj in deelnemer_klas.objects.all():        # pragma: no cover
        obj.ag_voor_team_mag_aangepast_worden = (obj.is_handmatig_ag or obj.aanvangsgemiddelde < 0.001)
        obj.ag_voor_indiv = obj.aanvangsgemiddelde
        obj.ag_voor_team = obj.aanvangsgemiddelde

        obj.save(update_fields=['ag_voor_team_mag_aangepast_worden', 'ag_voor_indiv', 'ag_voor_team'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Competitie', 'm0033_einde_teams_aanmaken'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='ag_voor_indiv',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='ag_voor_team',
            field=models.DecimalField(decimal_places=3, default=0.0, max_digits=5),
        ),
        migrations.AddField(
            model_name='regiocompetitieschutterboog',
            name='ag_voor_team_mag_aangepast_worden',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(migreer_ag_velden),
    ]

# end of file
