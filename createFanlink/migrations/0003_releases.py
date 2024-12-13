# Generated by Django 5.1.2 on 2024-12-07 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('createFanlink', '0002_fanlinks_boomplay'),
    ]

    operations = [
        migrations.CreateModel(
            name='Releases',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('Label', models.CharField(blank=True, max_length=255, null=True)),
                ('Artists', models.CharField(blank=True, max_length=255, null=True)),
                ('Title', models.CharField(blank=True, max_length=255, null=True)),
                ('UPC', models.CharField(blank=True, max_length=255, null=True)),
                ('ReleaseDate', models.CharField(blank=True, max_length=255, null=True)),
                ('FanlinkSent', models.CharField(blank=True, max_length=255, null=True)),
                ('Status', models.CharField(blank=True, max_length=255, null=True)),
                ('Y', models.CharField(blank=True, max_length=255, null=True)),
                ('MissingLinks', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'ordering': ['id'],
            },
        ),
    ]