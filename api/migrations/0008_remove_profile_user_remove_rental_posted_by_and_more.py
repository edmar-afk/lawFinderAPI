# Generated by Django 5.0.6 on 2024-08-02 05:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_rental_vehicle_type_message'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='user',
        ),
        migrations.RemoveField(
            model_name='rental',
            name='posted_by',
        ),
        migrations.DeleteModel(
            name='Message',
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
        migrations.DeleteModel(
            name='Rental',
        ),
    ]