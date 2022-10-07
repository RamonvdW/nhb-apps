# -*- coding: utf-8 -*-

#  Copyright (c) 2022 Ramon van der Winkel.
#  All rights reserved.
#  Licensed under BSD-3-Clause-Clear. See LICENSE file for details.

from django.db import migrations, models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from BasisTypen.models import ORGANISATIE_IFAA, GESLACHT_ALLE


""" kopie van de functies uit de Sporter.Sporter klasse """


def bereken_wedstrijdleeftijd_wa(sporter, jaar):                                    # pragma: no cover
    """ Bereken de wedstrijdleeftijd voor dit lid volgens de WA regels
        De wedstrijdleeftijd is de leeftijd die je bereikt in het opgegeven jaar
    """
    # voorbeeld: geboren 2001, huidig jaar = 2019 --> leeftijd 18 wordt bereikt
    return jaar - sporter.geboorte_datum.year


def bereken_wedstrijdleeftijd_ifaa(sporter, datum_eerste_wedstrijddag):             # pragma: no cover
    """ Bereken de wedstrijdleeftijd voor dit lid volgens de IFAA regels
        De wedstrijdleeftijd is je leeftijd op de eerste dag van de wedstrijd
    """
    # voorbeeld: geboren 2001-10-08, datum_eerste_wedstrijddag = 2019-10-07 --> wedstrijdleeftijd is 17
    # voorbeeld: geboren 2001-10-08, datum_eerste_wedstrijddag = 2019-10-08 --> wedstrijdleeftijd is 18

    # ga uit van de te bereiken leeftijd dit jaar
    wedstrijdleeftijd = datum_eerste_wedstrijddag.year - sporter.geboorte_datum.year

    # vergelijk de wedstrijd datum en de verjaardag
    tup1 = (datum_eerste_wedstrijddag.month, datum_eerste_wedstrijddag.day)
    tup2 = (sporter.geboorte_datum.month, sporter.geboorte_datum.day)
    if tup1 < tup2:
        # nog voor de verjaardag
        wedstrijdleeftijd -= 1

    return wedstrijdleeftijd


def bereken_wedstrijdleeftijd(sporter, datum_eerste_wedstrijd, organisatie):        # pragma: no cover
    if organisatie == ORGANISATIE_IFAA:
        wedstrijdleeftijd = bereken_wedstrijdleeftijd_ifaa(sporter, datum_eerste_wedstrijd)
    else:
        wedstrijdleeftijd = bereken_wedstrijdleeftijd_wa(sporter, datum_eerste_wedstrijd.year)
    return wedstrijdleeftijd


""" kopie van de functies uit de BasisTypen.LeeftijdsKlasse """


def geslacht_is_compatible(lkl, wedstrijd_geslacht):                                # pragma: no cover
    """ past het wedstrijdgeslacht van de sporter bij deze leeftijdsklasse?

        leeftijdsklasse 'A' (alle) past bij alle wedstrijdgeslachten
        anders moet het een 'M'/'V' match zijn
    """
    return (lkl.wedstrijd_geslacht == GESLACHT_ALLE) or (wedstrijd_geslacht == lkl.wedstrijd_geslacht)


def leeftijd_is_compatible(lkl, wedstrijdleeftijd):         # pragma: no cover
    """ voldoet de wedstrijdleeftijd aan de eisen van deze wedstrijdklasse? """

    if wedstrijdleeftijd < lkl.min_wedstrijdleeftijd:
        # voldoet niet aan ondergrens
        return False

    if lkl.max_wedstrijdleeftijd and wedstrijdleeftijd > lkl.max_wedstrijdleeftijd:
        # voldoet niet aan de bovengrens
        return False

    # voldoet aan de eisen
    return True


def zet_inschrijving_klasse(apps, _):
    """ Bepaal voor elke inschrijving de wedstrijdklasse.
    """

    # zoek de klassen op voor deze migratie
    voorkeuren_klas = apps.get_model('Sporter', 'SporterVoorkeuren')
    inschrijving_klas = apps.get_model('Wedstrijden', 'WedstrijdInschrijving')

    # bepaal een redelijke klasse binnen de al gekozen sessie van de wedstrijd
    # vergelijkbare code is te vinden in view_inschrijven::get_sessies

    stamp_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d om %H:%M')

    for inschrijving in (inschrijving_klas
                         .objects
                         .select_related('wedstrijd',
                                         'sessie',
                                         'sporterboog',
                                         'sporterboog__sporter',
                                         'sporterboog__boogtype')
                         .all()):        # pragma: no cover
        wedstrijd = inschrijving.wedstrijd
        sessie = inschrijving.sessie
        wedstrijdboog_pk = inschrijving.sporterboog.boogtype.pk
        sporter = inschrijving.sporterboog.sporter

        try:
            voorkeuren = voorkeuren_klas.objects.get(sporter=sporter)
        except ObjectDoesNotExist:
            voorkeuren = None

        wedstrijdleeftijd = bereken_wedstrijdleeftijd(sporter, wedstrijd.datum_begin, wedstrijd.organisatie)

        wedstrijd_geslacht = '?'
        if voorkeuren and voorkeuren.wedstrijd_geslacht_gekozen:
            wedstrijd_geslacht = voorkeuren.wedstrijd_geslacht

        # verzamel een lijstje van compatibele wedstrijdklassen om uit te kiezen
        wedstrijdklassen = list()
        for klasse in sessie.wedstrijdklassen.select_related('leeftijdsklasse', 'boogtype').all():
            if klasse.boogtype.pk == wedstrijdboog_pk:
                # boog is compatibel
                lkl = klasse.leeftijdsklasse
                if geslacht_is_compatible(lkl, wedstrijd_geslacht):
                    # geslacht is compatible
                    if leeftijd_is_compatible(lkl, wedstrijdleeftijd):
                        # leeftijd is compatible
                        wedstrijdklassen.append(klasse)
        # for

        # print(inschrijving, '-->', repr([klasse.beschrijving for klasse in wedstrijdklassen]))

        # simpelste methode: kies de eerste (ook al zijn er meerdere keuzes)
        inschrijving.wedstrijdklasse = wedstrijdklassen[0]
        inschrijving.log += "[%s] Migratie koos wedstrijdklasse: %s\n" % (stamp_str,
                                                                          inschrijving.wedstrijdklasse.beschrijving)
        inschrijving.save(update_fields=['wedstrijdklasse', 'log'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('BasisTypen', 'm0046_wkl_refresh'),
        ('Wedstrijden', 'm0028_inschrijven_tot'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='wedstrijdinschrijving',
            name='wedstrijdklasse',
            field=models.ForeignKey(null=True, on_delete=models.deletion.PROTECT, to='BasisTypen.kalenderwedstrijdklasse'),
        ),
        migrations.AddField(
            model_name='wedstrijdinschrijving',
            name='log',
            field=models.TextField(blank=True),
        ),

        migrations.RunPython(zet_inschrijving_klasse, reverse_code=migrations.RunPython.noop),

        # nu alle klassen gezet zijn kan de null er weer vanaf
        migrations.AlterField(
            model_name='wedstrijdinschrijving',
            name='wedstrijdklasse',
            field=models.ForeignKey(default=None, on_delete=models.deletion.PROTECT, to='BasisTypen.kalenderwedstrijdklasse'),
            preserve_default=False,
        ),
    ]

# end of file
