# Generated by Django 3.0.9 on 2021-02-02 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sources', '0011_auto_20210119_1439'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
