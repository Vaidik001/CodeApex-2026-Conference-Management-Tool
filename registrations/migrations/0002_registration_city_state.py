from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='city',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='registration',
            name='state',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
