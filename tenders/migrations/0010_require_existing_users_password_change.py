from django.conf import settings
from django.db import migrations


def require_existing_users_password_change(apps, schema_editor):
    user_model = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    security_profile_model = apps.get_model('tenders', 'UserSecurityProfile')
    for user_id in user_model.objects.values_list('id', flat=True).iterator():
        security_profile_model.objects.update_or_create(
            user_id=user_id,
            defaults={'must_change_password': True},
        )


class Migration(migrations.Migration):
    dependencies = [
        ('tenders', '0009_usersecurityprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(
            require_existing_users_password_change,
            migrations.RunPython.noop,
        ),
    ]
