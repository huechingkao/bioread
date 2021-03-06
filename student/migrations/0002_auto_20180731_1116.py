# Generated by Django 2.0.5 on 2018-07-31 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_id', models.IntegerField(default=0)),
                ('enroll_id', models.IntegerField(default=0)),
                ('group', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='studentgroup',
            unique_together={('enroll_id', 'group_id')},
        ),
    ]
