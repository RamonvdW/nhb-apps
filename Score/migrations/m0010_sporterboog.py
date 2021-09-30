# Generated by Django 3.1.13 on 2021-09-18 17:18

from django.db import migrations, models
import django.db.models.deletion


def migrate_sporterboog(apps, _):
    """ Voorzie elke Score van sporterboog naast schutterboog """

    # haal de klassen op
    score_klas = apps.get_model('Score', 'Score')
    sporterboog_klas = apps.get_model('Sporter', 'SporterBoog')

    # maak een cache
    cache = dict()      # [sporter.lid_nr] = SporterBoog
    for sporterboog in (sporterboog_klas
                        .objects
                        .select_related('sporter',
                                        'boogtype')
                        .all()):                                # pragma: no cover

        tup = (sporterboog.sporter.lid_nr, sporterboog.boogtype.afkorting)
        cache[tup] = sporterboog
    # for

    # voorzie elke Score van sporterboog
    for score in (score_klas
                  .objects
                  .select_related('schutterboog__nhblid',
                                  'schutterboog__boogtype')
                  .exclude(schutterboog__nhblid=None)
                  .all()):                                      # pragma: no cover

        tup = (score.schutterboog.nhblid.nhb_nr, score.schutterboog.boogtype.afkorting)
        score.sporterboog = cache[tup]
        score.save(update_fields=['sporterboog'])
    # for


class Migration(migrations.Migration):

    """ Migratie class voor dit deel van de applicatie """

    # volgorde afdwingen
    dependencies = [
        ('Sporter', 'm0002_copy_data'),
        ('Score', 'm0009_squashed'),
    ]

    # migratie functies
    operations = [
        migrations.AddField(
            model_name='score',
            name='sporterboog',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='Sporter.sporterboog'),
        ),
        migrations.AlterField(
            model_name='scorehist',
            name='score',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='Score.score'),
        ),
        migrations.RunPython(migrate_sporterboog),
        migrations.RemoveField(
            model_name='score',
            name='schutterboog')
    ]

# end of file
