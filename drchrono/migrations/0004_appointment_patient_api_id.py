# Generated by Django 2.2.6 on 2019-11-01 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drchrono', '0003_auto_20191101_1306'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='patient_api_id',
            field=models.IntegerField(default=0),
        ),
    ]
