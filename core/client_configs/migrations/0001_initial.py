# Generated by Django 3.0.9 on 2021-02-01 07:56

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(blank=True, null=True)),
                ('type', models.CharField(choices=[('home', 'Home')], default='home', max_length=255)),
                ('layout', models.CharField(choices=[('table', 'table'), ('list', 'List')], default='table', max_length=255)),
                ('page_size', models.IntegerField(default=25)),
                ('resource_id', models.PositiveIntegerField()),
                ('config', django.contrib.postgres.fields.jsonb.JSONField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='client_configs_clientconfig_related_created_by', related_query_name='client_configs_clientconfigs_created_by', to=settings.AUTH_USER_MODEL)),
                ('resource_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('updated_by', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='client_configs_clientconfig_related_updated_by', related_query_name='client_configs_clientconfigs_updated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'client_configurations',
            },
        ),
    ]