# from cloudinary.models import CloudinaryField
from cloudinary import models as cloudinary

from django.db import models
from django.contrib.auth import models as auth_models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from house_manager.accounts.managers import HouseManagerUserManager
from house_manager.accounts.validators import validate_profile_picture_size
from house_manager.common.mixins import TimeStampModel
from house_manager.common.validators import validate_char_field, validate_phone_number


class HouseManagerUser(auth_models.AbstractBaseUser, auth_models.PermissionsMixin):
    email = models.EmailField(
        _("email"),
        unique=True,
        error_messages={
            "unique": _("User with that email already exists."),
        },
    )

    is_staff = models.BooleanField(
        _("staff status"),
        default=True,
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    USERNAME_FIELD = "email"

    objects = HouseManagerUserManager()


class Profile(TimeStampModel):
    MAX_FIRST_NAME_LENGTH = 30
    MAX_LAST_NAME_LENGTH = 30
    MAX_PHONE_NUMBER_LENGTH = 10

    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
        blank=True,
        null=True,
        validators=[
            validate_char_field
        ],
        verbose_name=_("First name"),
    )

    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
        blank=True,
        null=True,
        validators=[
            validate_char_field
        ],
        verbose_name=_("Last name"),
    )

    phone_number = models.CharField(
        max_length=MAX_PHONE_NUMBER_LENGTH,
        blank=True,
        null=True,
        validators=[
            validate_phone_number,
        ],
        verbose_name=_("Phone number"),
    )

    profile_picture = cloudinary.CloudinaryField(
        _("Profile picture"),
        blank=True,
        null=True,
        validators=(
            validate_profile_picture_size,
        ),
    )

    user = models.OneToOneField(
        to=HouseManagerUser,
        primary_key=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.full_name}"

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"

        return self.first_name or self.last_name or ""

