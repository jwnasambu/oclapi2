# Generated by Django 3.0.9 on 2021-01-04 15:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('concepts', '0005_auto_20200923_0246'),
        ('mappings', '0008_auto_20210104_0626'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mapping',
            name='from_concept',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mappings_from', to='concepts.Concept'),
        ),
    ]
