from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from allauth.account.models import EmailAddress
from allauth.account.signals import password_reset

from house_manager.accounts.models import Profile

UserModel = get_user_model()


@receiver(post_save, sender=UserModel)
def user_created(sender, instance, created, **kwargs):
    if not created:
        return

    Profile.objects.create(user=instance)
    # No welcome email: registration sends the allauth confirmation email
    # (security #11) — a second mail would only dilute it.


@receiver(password_reset)
def mark_email_verified_on_password_reset(sender, request, user, **kwargs):
    # A completed reset proves mailbox ownership — the link was emailed to
    # the address and followed. Marking it verified here keeps the login
    # gate (which demands a verified email) from demanding a SECOND email
    # confirmation right after the reset.
    EmailAddress.objects.filter(user=user, email__iexact=user.email).update(
        verified=True
    )


@receiver(post_save, sender=UserModel)
def setup_custom_admin_group(sender, instance, created, **kwargs):
    if created and instance.is_superuser:
        # Create custom admin group if this is the first superuser
        existing_superusers = UserModel.objects.filter(is_superuser=True)
        if existing_superusers.count() == 1:
            custom_admin_group, created = Group.objects.get_or_create(name='StandardUser')

            # Add model names for which regular users will have CRUD operations
            allowed_models = [
                'House', 'Client', 'HouseMonthlyBill',
                'HouseOtherBill', 'ClientMonthlyBill',
                'ClientOtherBill'
            ]

            permissions = []
            for app_config in apps.get_app_configs():
                models = app_config.get_models()
                for model in models:
                    if model.__name__ in allowed_models:
                        content_type = ContentType.objects.get_for_model(model)
                        model_permissions = Permission.objects.filter(content_type=content_type)
                        permissions.extend(model_permissions)

            custom_admin_group.permissions.set(permissions)

    elif created and not instance.is_superuser:
        # Assign regular users to the custom admin group upon creation
        custom_admin_group, created = Group.objects.get_or_create(name='StandardUser')
        instance.groups.add(custom_admin_group)




