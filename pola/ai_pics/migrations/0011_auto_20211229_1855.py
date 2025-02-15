# Generated by Django 3.2.10 on 2021-12-29 17:55

import django.contrib.postgres.indexes
import django.utils.timezone
import model_utils.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_pics', '0010_auto_20211003_0556'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='aipics',
            name='ai_pics_aip_created_9179cd_brin',
        ),
        migrations.RenameField(
            model_name='aipics',
            old_name='created_at',
            new_name='created',
        ),
        migrations.AddField(
            model_name='aipics',
            name='modified',
            field=model_utils.fields.AutoLastModifiedField(
                default=django.utils.timezone.now, editable=False, verbose_name='modified'
            ),
        ),
        migrations.AlterField(
            model_name='aipics',
            name='created',
            field=model_utils.fields.AutoCreatedField(
                default=django.utils.timezone.now, editable=False, verbose_name='created'
            ),
        ),
        migrations.AddIndex(
            model_name='aipics',
            index=django.contrib.postgres.indexes.BrinIndex(
                fields=['created'], name='ai_pics_aip_created_96e607_brin', pages_per_range=16
            ),
        ),
    ]
