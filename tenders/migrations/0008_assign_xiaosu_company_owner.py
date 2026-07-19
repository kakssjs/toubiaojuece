from django.conf import settings
from django.db import migrations


def assign_xiaosu_owner(apps, schema_editor):
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    company_model = apps.get_model('tenders', 'CompanyProfile')
    user = user_model.objects.filter(username__iexact='xiaosukeji').first()
    if user is None:
        return

    company_model.objects.filter(
        name__contains='小苏',
        owner_id__isnull=True,
    ).update(owner_id=user.pk)


class Migration(migrations.Migration):
    dependencies = [
        ('tenders', '0007_companyprofile_owner'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(assign_xiaosu_owner, migrations.RunPython.noop),
    ]
