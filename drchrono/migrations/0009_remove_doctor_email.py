# Generated by Django 2.2.6 on 2019-11-03 08:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('drchrono', '0008_doctor_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='doctor',
            name='email',
        ),
    ]