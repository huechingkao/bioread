# Generated by Django 2.0.5 on 2018-08-04 04:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0003_sfcontent_sfreply_sfwork'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sfwork',
            name='index',
            field=models.IntegerField(default=0),
        ),
    ]