# Generated by Django 2.2.5 on 2019-10-02 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('findpairs', '0004_game_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='state',
            field=models.TextField(default=''),
        ),
    ]
