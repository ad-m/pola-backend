# Generated by Django 3.1.6 on 2021-02-15 06:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0022_auto_20210117_0109'),
    ]

    operations = [
        migrations.AlterField(
            model_name='brand',
            name='name',
            field=models.CharField(
                blank=True, db_index=True, max_length=128, null=True, verbose_name='Nazwa marki (na podstawie ILiM)'
            ),
        ),
    ]
