"""Security #11 rollout: existing users predate email verification.

Their accounts were created by the old registration flow, which never
created allauth EmailAddress rows. With ACCOUNT_EMAIL_VERIFICATION now
'mandatory', a missing/verified record would wall every existing user
out at next login. The chosen rollout (per review) trusts the existing
accounts: each user gets a primary, VERIFIED EmailAddress row. New
signups still start unverified and must confirm the emailed link.
"""

from django.db import migrations


def backfill_verified_emails(apps, schema_editor):
    User = apps.get_model("accounts", "HouseManagerUser")
    EmailAddress = apps.get_model("account", "EmailAddress")

    existing_emails = set(EmailAddress.objects.values_list("email", flat=True))
    missing = [
        EmailAddress(
            user_id=user.pk,
            email=user.email,
            primary=True,
            verified=True,
        )
        for user in User.objects.exclude(email__in=existing_emails)
    ]
    EmailAddress.objects.bulk_create(missing, batch_size=500, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_housemanageruser_has_set_password"),
        ("account", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(backfill_verified_emails, migrations.RunPython.noop),
    ]
