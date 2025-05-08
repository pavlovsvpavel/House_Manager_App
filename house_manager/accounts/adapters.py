from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages
UserModel = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if the user is already logged in
        if request.user.is_authenticated:
            return

        # Get the email from the social login
        email = sociallogin.account.extra_data.get('email')

        # Check if a user with this email already exists and has set personal password
        if email:
            user = UserModel.objects.filter(email=email).first()
            if user and user.has_set_password:
                messages.error(request,
                               "An account with this email already exists. "
                               "Please log in with your email and password.")
                raise ImmediateHttpResponse(redirect('login_user'))