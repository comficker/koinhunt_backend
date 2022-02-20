# Generated by Django 3.2.5 on 2022-02-04 17:36

import apps.media.models
from django.db import migrations, models
import django.utils.timezone
import sorl.thumbnail.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('updated', models.DateTimeField(default=django.utils.timezone.now)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
                ('db_status', models.IntegerField(choices=[(-1, 'Deleted'), (0, 'Pending'), (1, 'Active')], default=1)),
                ('title', models.CharField(blank=True, max_length=120)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('path', sorl.thumbnail.fields.ImageField(max_length=500, upload_to=apps.media.models.path_and_rename, validators=[apps.media.models.validate_file_size])),
            ],
            options={
                'abstract': False,
            },
        ),
    ]