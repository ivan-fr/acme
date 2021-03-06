# Generated by Django 2.1 on 2018-08-22 17:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publication', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-created', '-updated'), 'verbose_name_plural': 'entries'},
        ),
        migrations.AlterModelOptions(
            name='flatpage',
            options={'ordering': ('-created', '-updated')},
        ),
        migrations.RemoveField(
            model_name='entry',
            name='publish',
        ),
        migrations.RemoveField(
            model_name='flatpage',
            name='publish',
        ),
        migrations.AddField(
            model_name='entry',
            name='created',
            field=models.DateTimeField(default=None, editable=False),
        ),
        migrations.AddField(
            model_name='flatpage',
            name='created',
            field=models.DateTimeField(default=None, editable=False),
        ),
        migrations.AlterField(
            model_name='entry',
            name='updated',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='flatpage',
            name='updated',
            field=models.DateTimeField(),
        ),
    ]
