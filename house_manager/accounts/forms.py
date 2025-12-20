from django import forms
from django.contrib.auth import forms as auth_forms, get_user_model
from django.contrib.auth.forms import SetPasswordForm, AuthenticationForm
from django.core.exceptions import ValidationError
import requests
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

from house_manager import settings

UserModel = get_user_model()


# class HouseManagerUserCreationForm(auth_forms.UserCreationForm):
#     user = None
#     usable_password = None
#
#     class Meta(auth_forms.UserCreationForm.Meta):
#         model = UserModel
#         fields = ('email',)
#
#     recaptcha = ReCaptchaField(widget=ReCaptchaV2Checkbox, required=True)

class HouseManagerUserLoginForm(AuthenticationForm):
    def clean(self):
        recaptcha_response = self.request.POST.get('g-recaptcha-response-login')

        if not recaptcha_response:
            raise ValidationError("reCAPTCHA check missing. Refresh and try again.")

        secret_key = settings.RECAPTCHA_PRIVATE_KEY
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            'secret': secret_key,
            'response': recaptcha_response,
        }

        try:
            response = requests.post(verify_url, data=payload)
            result = response.json()

            # --- TEST OVERRIDE (Remove this in production) ---
            # print(f"Actual Google Score: {result.get('score')}")
            # result['score'] = 0.0
            # -------------------------------------------------

        except requests.RequestException:
            raise ValidationError("Connection to reCAPTCHA failed.")

        if not result.get('success') or result.get('score', 0) < 0.4:
            raise ValidationError("Login failed. Our system suspects you might be a bot.")

        cleaned_data = super().clean()

        return cleaned_data


class HouseManagerUserCreationForm(auth_forms.UserCreationForm):
    class Meta(auth_forms.UserCreationForm.Meta):
        model = UserModel
        fields = ('email',)

    def clean(self):
        recaptcha_response = self.data.get('g-recaptcha-response-register')

        if not recaptcha_response:
            raise ValidationError("reCAPTCHA check missing. Please refresh and try again.")

        secret_key = settings.RECAPTCHA_PRIVATE_KEY
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            'secret': secret_key,
            'response': recaptcha_response,
        }

        try:
            response = requests.post(verify_url, data=payload)
            result = response.json()

            # --- TEST OVERRIDE (Remove this in production) ---
            # print(f"Actual Google Score: {result.get('score')}")
            # result['score'] = 0.0
            # -------------------------------------------------

        except requests.RequestException:
            raise ValidationError("Unable to connect to reCAPTCHA service.")

        if not result.get('success') or result.get('score', 0) < 0.6:
            raise ValidationError("Registration failed. Our system suspects you might be a bot.")

        cleaned_data = super().clean()

        return cleaned_data


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
