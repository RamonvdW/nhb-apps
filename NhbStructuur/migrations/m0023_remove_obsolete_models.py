# Generated by Django 3.1.13 on 2021-10-02 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('NhbStructuur', 'm0022_delete_migrated_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='speelsterkte',
            name='lid',
        ),
        migrations.RemoveField(
            model_name='nhbvereniging',
            name='contact_email',
        ),
        migrations.RemoveField(
            model_name='nhbvereniging',
            name='secretaris_lid',
        ),
        migrations.DeleteModel(
            name='NhbLid',
        ),
        migrations.DeleteModel(
            name='Speelsterkte',
        ),
    ]
