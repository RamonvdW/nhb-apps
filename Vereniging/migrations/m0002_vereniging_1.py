# -*- coding: utf-8 -*-

#  Copyright (c) 2023 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models


def add_vereniging_new(apps, _):
    """ migratie van veld vereniging """

    ver_klas = apps.get_model('Vereniging', 'Vereniging')
    sec_klas = apps.get_model('Vereniging', 'Secretaris')

    # maak een cache
    ver_nr2ver = dict()     # [ver_nr] = Vereniging()
    for ver in ver_klas.objects.all():
        ver_nr2ver[ver.ver_nr] = ver
    # for

    for sec in sec_klas.objects.select_related('vereniging'):
        sec.vereniging_new = ver_nr2ver[sec.vereniging.ver_nr]
        sec.save(update_fields=['vereniging_new'])
    # for


def copy_nhb_ver(apps, _):

    # haal de klassen op die van toepassing zijn tijdens deze migratie
    old_ver_klas = apps.get_model('NhbStructuur', 'NhbVereniging')
    new_ver_klas = apps.get_model('Vereniging', 'Vereniging')

    ver2clusters = dict()       # [ver] = clusters

    # kopieer alle verenigingen
    bulk = list()
    for old_ver in old_ver_klas.objects.select_related('regio').prefetch_related('clusters').all():
        new_ver = new_ver_klas(
                    ver_nr=old_ver.ver_nr,
                    naam=old_ver.naam,
                    adres_regel1=old_ver.adres_regel1,
                    adres_regel2=old_ver.adres_regel2,
                    plaats=old_ver.plaats,
                    regio=old_ver.regio,
                    geen_wedstrijden=old_ver.geen_wedstrijden,
                    is_extern=old_ver.is_extern,
                    kvk_nummer=old_ver.kvk_nummer,
                    website=old_ver.website,
                    contact_email=old_ver.contact_email,
                    telefoonnummer=old_ver.telefoonnummer,
                    bank_iban=old_ver.bank_iban,
                    bank_bic=old_ver.bank_bic)
        bulk.append(new_ver)

        ver2clusters[old_ver.ver_nr] = old_ver.clusters.all()
    # for

    new_ver_klas.objects.bulk_create(bulk)

    # clusters overnemen
    for new_ver in bulk:
        new_ver.clusters.set(ver2clusters[new_ver.ver_nr])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('NhbStructuur', 'm0034_squashed'),
        ('Registreer', 'm0005_squashed'),
        ('Vereniging', 'm0001_initial'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='Vereniging',
            fields=[
                ('ver_nr', models.PositiveIntegerField(primary_key=True, serialize=False)),
                ('naam', models.CharField(max_length=50)),
                ('adres_regel1', models.CharField(blank=True, default='', max_length=50)),
                ('adres_regel2', models.CharField(blank=True, default='', max_length=50)),
                ('plaats', models.CharField(blank=True, max_length=35)),
                ('geen_wedstrijden', models.BooleanField(default=False)),
                ('is_extern', models.BooleanField(default=False)),
                ('kvk_nummer', models.CharField(blank=True, default='', max_length=15)),
                ('website', models.CharField(blank=True, default='', max_length=100)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('telefoonnummer', models.CharField(blank=True, default='', max_length=20)),
                ('bank_iban', models.CharField(blank=True, default='', max_length=18)),
                ('bank_bic', models.CharField(blank=True, default='', max_length=11)),
                ('clusters', models.ManyToManyField(blank=True, to='NhbStructuur.nhbcluster')),
                ('regio', models.ForeignKey(on_delete=models.deletion.PROTECT, to='NhbStructuur.nhbregio')),
            ],
            options={
                'verbose_name': 'Vereniging',
                'verbose_name_plural': 'Verenigingen',
            },
        ),
        migrations.RunPython(copy_nhb_ver, migrations.RunPython.noop),
        migrations.AddField(
            model_name='secretaris',
            name='vereniging_new',
            field=models.ForeignKey(null=True, on_delete=models.deletion.CASCADE, to='Vereniging.vereniging'),
        ),
        migrations.RunPython(add_vereniging_new, migrations.RunPython.noop),
    ]

# end of file
