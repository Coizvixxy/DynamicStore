# Generated by Django 5.1.4 on 2025-01-14 04:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_category_image_category_created_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='business_address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='business_registration',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='position',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='store_banner',
            field=models.ImageField(blank=True, null=True, upload_to='store_banners/'),
        ),
        migrations.AddField(
            model_name='vendor',
            name='store_category',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='vendor',
            name='store_logo',
            field=models.ImageField(blank=True, null=True, upload_to='store_logos/'),
        ),
    ]
