# Generated by Django 5.1.5 on 2025-02-15 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_ordering', '0003_alter_userprofile_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='full_name',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
