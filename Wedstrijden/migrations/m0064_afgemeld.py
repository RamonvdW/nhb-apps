# -*- coding: utf-8 -*-

#  Copyright (c) 2026 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.utils import timezone
from decimal import Decimal
import datetime

WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD = 'A'  # op verzoek afgemeld, was voorheen definitief
WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD = 'V'  # uit mandje verwijderd, was nooit definitief


def maak_afgemeld(apps, _):

    """ vertaal WedstrijdInschrijving met status=afgemeld naar WedstrijdAfgemeld """

    klas_inschrijving = apps.get_model('Wedstrijden', 'WedstrijdInschrijving')
    klas_afgemeld = apps.get_model('Wedstrijden', 'WedstrijdAfgemeld')

    # verwijderd wordt al een tijdje niet meer bijgehouden, dus kan helemaal weg
    klas_inschrijving.objects.filter(status=WEDSTRIJD_INSCHRIJVING_STATUS_VERWIJDERD).delete()

    remove_pks = list()

    # afgemeld omzetten
    bulk = list()
    for inschrijving in (klas_inschrijving
                        .objects
                        .filter(status=WEDSTRIJD_INSCHRIJVING_STATUS_AFGEMELD)
                        .select_related('sessie')):

        remove_pks.append(inschrijving.pk)

        sessie = inschrijving.sessie
        if sessie:
            sessie_str = "%s om %s" % (sessie.datum, sessie.tijd_begin)
            if sessie.beschrijving:
                sessie_str += ' (%s)' % sessie.beschrijving
        else:
            sessie_str = ''

        afgemeld = klas_afgemeld(
                        wanneer_inschrijving=inschrijving.wanneer,
                        reserveringsnummer=inschrijving.pk,
                        wedstrijd=inschrijving.wedstrijd,
                        sessie=sessie_str,
                        sporterboog=inschrijving.sporterboog,
                        wedstrijdklasse=inschrijving.wedstrijdklasse,
                        bestelling_regel=inschrijving.bestelling_regel,
                        koper=inschrijving.koper,
                        bedrag_ontvangen=inschrijving.ontvangen_euro,
                        bedrag_retour=inschrijving.retour_euro,
                        log=inschrijving.log)

        # [2026-04-20 om 09:42] Afgemeld voor de wedstrijd
        pos = inschrijving.log.find('Afgemeld voor de wedstrijd')

        if pos > 0:
            when = inschrijving.log[pos-21:pos-2]
            when = when[:11] + when[-5:]
            when = datetime.datetime.strptime(when, '%Y-%m-%d %H:%M')
            when = timezone.make_aware(when, timezone=timezone.get_current_timezone())
            afgemeld.wanneer_afgemeld = when
        else:
            print('[ERROR] inschrijving pk=%s met status %s' % (inschrijving.pk, inschrijving.status))
            print('[ERROR] log: %s' % inschrijving.log)
            krak

        bulk.append(afgemeld)
    # for

    klas_afgemeld.objects.bulk_create(bulk)

    if len(remove_pks):
        klas_inschrijving.objects.filter(pk__in=remove_pks).delete()


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Account', 'm0032_squashed'),
        ('BasisTypen', 'm0062_squashed'),
        ('Bestelling', 'm0013_squashed'),
        ('Sporter', 'm0033_squashed'),
        ('Wedstrijden', 'm0063_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.CreateModel(
            name='WedstrijdAfgemeld',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('wanneer_inschrijving', models.DateTimeField()),
                ('reserveringsnummer', models.BigIntegerField()),
                ('wanneer_afgemeld', models.DateTimeField()),
                ('sessie', models.CharField(default='', max_length=100)),
                ('bedrag_ontvangen', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('bedrag_retour', models.DecimalField(decimal_places=2, default=Decimal('0'), max_digits=5)),
                ('log', models.TextField(blank=True)),
                ('bestelling', models.ForeignKey(null=True,
                                                 on_delete=models.deletion.PROTECT, to='Bestelling.bestellingregel')),
                ('koper', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Account.account')),
                ('korting', models.ForeignKey(blank=True, null=True,
                                              on_delete=models.deletion.SET_NULL, to='Wedstrijden.wedstrijdkorting')),
                ('sporterboog', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Sporter.sporterboog')),
                ('wedstrijd', models.ForeignKey(on_delete=models.deletion.PROTECT, to='Wedstrijden.wedstrijd')),
                ('wedstrijdklasse', models.ForeignKey(on_delete=models.deletion.PROTECT,
                                                      to='BasisTypen.kalenderwedstrijdklasse')),
            ],
            options={
                'verbose_name': 'Wedstrijd afmelding',
                'verbose_name_plural': 'Wedstrijd afmeldingen',
            },
        ),
        migrations.RunPython(maak_afgemeld, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='wedstrijdinschrijving',
            name='status',
            field=models.CharField(choices=[('R', 'Reservering'), ('B', 'Besteld'), ('D', 'Definitief')], default='R',
                                   max_length=2),
        ),
    ]

# end of file
