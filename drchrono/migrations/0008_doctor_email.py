# Generated by Django 2.2.6 on 2019-11-03 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drchrono', '0007_auto_20191102_0903'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
    ]