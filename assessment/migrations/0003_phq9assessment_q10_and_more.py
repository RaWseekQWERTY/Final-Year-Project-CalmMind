# Generated by Django 5.1.4 on 2025-03-03 13:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0002_alter_phq9assessment_depression_level_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='phq9assessment',
            name='q10',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='phq9assessment',
            name='assessment_date',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
