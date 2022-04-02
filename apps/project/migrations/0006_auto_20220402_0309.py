# Generated by Django 3.2.5 on 2022-04-02 03:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_project_socials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_date_end',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_date_start',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_name',
            field=models.CharField(db_index=True, default='launch', max_length=40),
        ),
        migrations.AlterField(
            model_name='project',
            name='id_string',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='project',
            name='terms',
            field=models.ManyToManyField(blank=True, db_index=True, related_name='projects', through='project.ProjectTerm', to='project.Term'),
        ),
    ]
