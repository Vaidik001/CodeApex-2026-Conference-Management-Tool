from django.db import migrations, models


def backfill_codes(apps, schema_editor):
    Conference = apps.get_model('conferences', 'Conference')
    dept_prefix_map = {
        'Computer Science & Engineering': 'CSE',
        'Electronics & Communication Engineering': 'ECE',
        'Mechanical Engineering': 'ME',
        'Civil Engineering': 'CE',
        'Electrical Engineering': 'EE',
        'Information Technology': 'IT',
        'Management': 'MGT',
    }
    for conf in Conference.objects.all().order_by('id'):
        if conf.code:
            continue
        year = conf.start_date.year if conf.start_date else 2026
        dept_name = conf.department.name if conf.department_id else ''
        prefix = dept_prefix_map.get(dept_name, 'GEN')
        conf.code = f'CMT-{year}-{prefix}-{conf.id:03d}'
        conf.save(update_fields=['code'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('conferences', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='code',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Auto-generated conference code, e.g. CMT-2026-CSE-001',
                max_length=30,
            ),
        ),
        migrations.RunPython(backfill_codes, noop_reverse),
        migrations.AlterField(
            model_name='conference',
            name='code',
            field=models.CharField(
                blank=True,
                help_text='Auto-generated conference code, e.g. CMT-2026-CSE-001',
                max_length=30,
                unique=True,
            ),
        ),
    ]
