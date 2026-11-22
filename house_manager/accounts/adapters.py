from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _

UserModel = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Check if the user is already logged in
        if request.user.is_authenticated:
            return

        # Security #11: decide on PROVIDER-VERIFIED emails only — extra_data
        # is provider-shaped and untrustworthy. A matching local account
        # with a password keeps its email+password workflow: the social
        # login is refused instead of silently linking the two accounts.
        verified_emails = [
            email_address.email
            for email_address in sociallogin.email_addresses
            if email_address.verified
        ]
        if verified_emails and UserModel.objects.filter(
            email__in=verified_emails,
            has_set_password=True,
        ).exists():
            messages.error(request,
                           _("An account with this email already exists. "
                             "Please log in with your email and password."))
            raise ImmediateHttpResponse(redirect('login_user'))
