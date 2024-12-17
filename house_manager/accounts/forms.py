from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.contrib.auth.forms import SetPasswordForm

UserModel = get_user_model()


class HouseManagerUserCreationForm(auth_forms.UserCreationForm):
    user = None
    usable_password = None

    class Meta(auth_forms.UserCreationForm.Meta):
        model = UserModel
        fields = ('email',)


class HouseManagerUserChangeForm(auth_forms.UserChangeForm):
    class Meta(auth_forms.UserChangeForm.Meta):
        model = UserModel


# View for setting a password when user is registered/first login via Google OAuth
class HouseManagerUserSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
    )
