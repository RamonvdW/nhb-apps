# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from BasisTypen.models import ORGANISATIE_NAT


def zet_organisatie(apps, _):
    """ zet het nieuwe organisatie veld """

    # alle bestaande bogen zijn World Archery en dat is ook de default, dus niets aan te passen
    boogtype_klas = apps.get_model('BasisTypen', 'BoogType')

    # R, C en BB zijn officiële WA team typen, de rest is nationaal - deze zijn default al op WA gezet
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        teamtype_klas = apps.get_model('BasisTypen', 'TeamType')

        for teamtype in teamtype_klas.objects.filter(volgorde__in=(4, 5)):
            # volgorde: 4 = IB en TR; 5 = LB
            teamtype.organisatie = ORGANISATIE_NAT
            teamtype.save(update_fields=['organisatie'])
        # for

    # bij de leeftijdsklassen kunnen we het bestaande veld 'volgens_wa' gebruiken
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        leeftijd_klas = apps.get_model('BasisTypen', 'LeeftijdsKlasse')

        for lkl in leeftijd_klas.objects.all():
            if not lkl.volgens_wa:
                lkl.organisatie = ORGANISATIE_NAT
                lkl.save(update_fields=['organisatie'])
        # for

    # de kalenderklassen verwijzen naar een leeftijdsklasse, waarvan we 'volgens_wa' weer kunnen overnemen
    if True:
        # haal de klassen op die van toepassing zijn tijdens deze migratie
        kalender_klas = apps.get_model('BasisTypen', 'KalenderWedstrijdklasse')

        for kal in kalender_klas.objects.select_related('leeftijdsklasse'):
            if not kal.leeftijdsklasse.volgens_wa:
                kal.organisatie = ORGANISATIE_NAT
                kal.save(update_fields=['organisatie'])
        # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0029_template'),
    ]

    # migratie functies
    operations = [
        migrations.AlterField(
            model_name='leeftijdsklasse',
            name='wedstrijd_geslacht',
            field=models.CharField(choices=[('M', 'Man'), ('V', 'Vrouw'), ('A', 'Gender neutraal')], max_length=1),
        ),
        migrations.AddField(
            model_name='boogtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AddField(
            model_name='kalenderwedstrijdklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AddField(
            model_name='leeftijdsklasse',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.AddField(
            model_name='teamtype',
            name='organisatie',
            field=models.CharField(choices=[('W', 'World Archery'), ('N', 'Nationaal'), ('F', 'IFAA')], default='W', max_length=1),
        ),
        migrations.RunPython(zet_organisatie),
        migrations.RemoveField(
            model_name='leeftijdsklasse',
            name='volgens_wa',
        ),
    ]

# end of file
