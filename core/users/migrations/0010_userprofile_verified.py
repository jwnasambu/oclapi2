# Generated by Django 3.0.9 on 2021-01-25 06:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20210115_0823'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='verified',
            field=models.BooleanField(default=True),
        ),
    ]
