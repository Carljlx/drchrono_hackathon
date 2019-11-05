# Generated by Django 2.2.6 on 2019-11-02 09:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drchrono', '0006_appointment_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='time_waited',
            new_name='duration',
        ),
        migrations.AddField(
            model_name='appointment',
            name='waiting_time',
            field=models.DurationField(null=True),
        ),
    ]