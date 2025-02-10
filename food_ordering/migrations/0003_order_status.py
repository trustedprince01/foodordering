# Generated by Django 5.1.5 on 2025-02-01 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food_ordering', '0002_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Pending', max_length=10),
        ),
    ]
