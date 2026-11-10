# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations


def corrigeer(apps, _):
    voorwaarden_klas = apps.get_model('Spelden', 'SpeldVoorwaarden')

    voorwaarden_klas.objects.filter(wedstrijd_soort='25m ronde').update(aantal_pijlen=60)
    voorwaarden_klas.objects.filter(wedstrijd_soort='18m ronde (Barebow)').update(wedstrijd_soort='Barebow 18m ronde')
    voorwaarden_klas.objects.filter(wedstrijd_soort='50m Barebow ronde').update(wedstrijd_soort='Barebow 50m ronde')
    voorwaarden_klas.objects.filter(wedstrijd_soort='50m Compound ronde').update(wedstrijd_soort='Compound 50m ronde')

    voorwaarden_klas.objects.filter(wedstrijd_soort='Barebow 50m ronde', speld__volgorde=3003, benodigde_score=520).update(benodigde_score=550)
    voorwaarden_klas.objects.filter(wedstrijd_soort='Barebow 50m ronde', speld__volgorde=3004, benodigde_score=540).update(benodigde_score=600)
    voorwaarden_klas.objects.filter(wedstrijd_soort='Barebow 50m ronde', speld__volgorde=3005, benodigde_score=550).update(benodigde_score=625)
    voorwaarden_klas.objects.filter(wedstrijd_soort='Barebow 50m ronde', speld__volgorde=3006, benodigde_score=560).update(benodigde_score=640)


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Spelden', 'm0008_aanvraagprep'),
    ]

    # migratie functies
    operations = [
        migrations.RemoveField(
            model_name='speldtoegekend',
            name='category',
        ),
        migrations.RunPython(corrigeer, reverse_code=migrations.RunPython.noop),
    ]

# end of file
