from datetime import timedelta
import re
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sites.models import Site
from django.core import mail
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from allauth.account.models import EmailAddress

from house_manager.accounts.adapters import CustomSocialAccountAdapter
from allauth.socialaccount.models import SocialApp

from house_manager.accounts.adapters import CustomSocialAccountAdapter

UserModel = get_user_model()


def _recaptcha_ok():
    """
    The login/register forms verify a reCAPTCHA token against Google;
    the tests stub that call out (the rig has no widget interaction).
    """
    response = mock.Mock()
    response.json.return_value = {"success": True, "score": 0.9}
    return mock.patch("house_manager.accounts.forms.requests.post", return_value=response)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailVerificationFlowTests(TestCase):
    """
    Security #11: accounts are unusable until the emailed confirmation
    link is followed — registering no longer logs the user in, and the
    login view refuses accounts with an unverified email.
    """

    @classmethod
    def setUpTestData(cls):
        cls.register_url = reverse("register_user")
        cls.login_url = reverse("login_user")
        cls.verification_sent_url = reverse("account_email_verification_sent")

    def _register(self, email="new@test.bg"):
        with _recaptcha_ok():
            return self.client.post(self.register_url, data={
                "email": email,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "g-recaptcha-response-register": "test-token",
            })

    def test_register_sends_confirmation_and_does_not_log_in(self):
        response = self._register()

        self.assertRedirects(response, self.verification_sent_url, fetch_redirect_response=False)
        user = UserModel.objects.get(email="new@test.bg")
        self.assertTrue(user.has_set_password)
        address = EmailAddress.objects.get(user=user)
        self.assertFalse(address.verified)
        # Exactly one mail: the confirmation. (The old "successful
        # registration" welcome mail is gone — it only diluted it.)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("new@test.bg", mail.outbox[0].to)
        self.assertIn("confirm-email/", mail.outbox[0].body)
        # No immediate login anymore: the register response must not authenticate.
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_confirm_link_verifies_and_logs_in(self):
        self._register()

        # HMAC mode: the key exists only in the emailed link.
        key = re.search(r"confirm-email/([^/\s]+)/", mail.outbox[0].body).group(1)
        confirm_url = reverse("account_confirm_email", args=[key])

        # The landing page shows the address and a confirm button...
        page = self.client.get(confirm_url)
        self.assertContains(page, "new@test.bg")

        # ...and confirming verifies the address, then sends the user to
        # the login page (allauth deliberately does not auto-login on an
        # emailed link — links live in mailboxes and logs).
        response = self.client.post(confirm_url)
        self.assertTrue(EmailAddress.objects.get(email="new@test.bg").verified)
        self.assertRedirects(response, reverse("account_login"), fetch_redirect_response=False)

        # The gate now passes: the user logs in.
        with _recaptcha_ok():
            self.client.post(self.login_url, data={
                "username": "new@test.bg",
                "password": "StrongPass123!",
                "g-recaptcha-response-login": "test-token",
            })
        self.assertIn("_auth_user_id", self.client.session)

    def test_unverified_login_is_blocked_and_resends_with_cooldown(self):
        self._register()
        mail.outbox.clear()
        # The registration's own send armed the cooldown; expire it so the
        # login attempt sends a fresh link.
        cache.clear()

        with _recaptcha_ok():
            response = self.client.post(self.login_url, data={
                "username": "new@test.bg",
                "password": "StrongPass123!",
                "g-recaptcha-response-login": "test-token",
            })

        self.assertRedirects(response, self.verification_sent_url, fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)  # a fresh link went out

        # Immediate retry: the cooldown holds, no extra email floods the inbox.
        with _recaptcha_ok():
            self.client.post(self.login_url, data={
                "username": "new@test.bg",
                "password": "StrongPass123!",
                "g-recaptcha-response-login": "test-token",
            })
        self.assertEqual(len(mail.outbox), 1)

    def test_verified_user_can_log_in(self):
        self._register()
        EmailAddress.objects.update(verified=True)

        with _recaptcha_ok():
            response = self.client.post(self.login_url, data={
                "username": "new@test.bg",
                "password": "StrongPass123!",
                "g-recaptcha-response-login": "test-token",
            })

        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)


class LogoutMethodTests(TestCase):
    """Security #10: logout is POST-only (a GET link is CSRF-able)."""

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(email="out@test.bg", password="StrongPass123!")

    def test_get_logout_is_not_allowed(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse("logout_user"))

        self.assertEqual(response.status_code, 405)
        # The session must survive a GET attempt.
        self.assertIn("_auth_user_id", self.client.session)

    def test_post_logout_clears_session(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse("logout_user"))

        self.assertRedirects(response, reverse("index"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


class SocialLoginUITests(TestCase):
    """Security #10: with SOCIALACCOUNT_LOGIN_ON_GET off, the Google button is a POST form."""

    @classmethod
    def setUpTestData(cls):
        app = SocialApp.objects.create(
            provider="google", name="Google", client_id="test", secret="test"
        )
        app.sites.add(Site.objects.get_current())

    def test_google_login_is_posted(self):
        response = self.client.get(reverse("login_user"))

        self.assertContains(response, 'method="post"')
        self.assertContains(response, "/accounts/google/login/")
        self.assertNotContains(response, '<a href="/accounts/google/login/')


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetFlowTests(TestCase):
    """
    Security #11 follow-up: the reset flow exists only for accounts with a
    personal password. A reset request for a Google-only account behaves
    like an unknown account — generic response, no reset link.
    """

    @classmethod
    def setUpTestData(cls):
        cls.owner = UserModel.objects.create_user(email="reset@test.bg", password="OldPass123!")
        cls.owner.has_set_password = True
        cls.owner.save(update_fields=["has_set_password"])
        cls.social_only = UserModel.objects.create_user(email="social@test.bg", password=None)

    def _request_reset(self, email):
        return self.client.post(reverse("account_reset_password"), data={"email": email})

    def _reset_url(self):
        return re.search(r"https?://\S*password/reset/key/\S+", mail.outbox[0].body).group(0)

    def test_password_user_receives_link_and_resets(self):
        response = self._request_reset("reset@test.bg")

        self.assertRedirects(response, reverse("account_reset_password_done"), fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@test.bg", mail.outbox[0].to)

        set_url = self._reset_url().replace("http://testserver", "")
        # allauth's stage flow: the emailed key validates and redirects to a
        # session-scoped set-password path.
        response = self.client.get(set_url)
        if response.status_code == 302:
            set_url = response["Location"].replace("http://testserver", "")
        self.assertContains(self.client.get(set_url), "Set a new password")
        response = self.client.post(set_url, data={
            "password1": "NewPass456!",
            "password2": "NewPass456!",
        })

        self.assertRedirects(response, reverse("account_reset_password_from_key_done"), fetch_redirect_response=False)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.has_usable_password())

        # The new password works through the (verification-passing) gate —
        # the completed reset proved mailbox ownership, which the
        # password_reset signal handler turns into a verified address.
        with _recaptcha_ok():
            self.client.post(reverse("login_user"), data={
                "username": "reset@test.bg",
                "password": "NewPass456!",
                "g-recaptcha-response-login": "test-token",
            })
        self.assertIn("_auth_user_id", self.client.session)

    def test_google_only_email_gets_no_reset_link(self):
        response = self._request_reset("social@test.bg")

        # No enumeration: the same generic "check your email" page...
        self.assertRedirects(response, reverse("account_reset_password_done"), fetch_redirect_response=False)
        # ...and no reset link in the outbox (allauth may send its
        # "unknown account" notification, which carries no reset URL).
        for message in mail.outbox:
            self.assertNotIn("password/reset/key/", message.body)


class SocialAccountLinkingTests(TestCase):
    """
    Security #11: the social adapter decides on provider-verified emails
    only, and refuses to link a matching local account that has a password.
    """

    def setUp(self):
        self.adapter = CustomSocialAccountAdapter()
        self.request = RequestFactory().post(reverse("login_user"))
        self.request.session = {}
        self.request.user = AnonymousUser()
        setattr(self.request, "_messages", FallbackStorage(self.request))

    def _sociallogin(self, email, verified=True):
        return SimpleNamespace(
            email_addresses=[SimpleNamespace(email=email, verified=verified)]
        )

    def _assert_refused(self, sociallogin):
        from allauth.core.exceptions import ImmediateHttpResponse

        with self.assertRaises(ImmediateHttpResponse) as ctx:
            self.adapter.pre_social_login(self.request, self._sociallogin(sociallogin))
        self.assertEqual(ctx.exception.response.status_code, 302)
        self.assertIn("already exists", str(list(self.request._messages)[0]))

    def test_verified_email_matching_password_account_is_refused(self):
        user = UserModel.objects.create_user(email="pair@test.bg", password="StrongPass123!")
        user.has_set_password = True
        user.save(update_fields=["has_set_password"])

        self._assert_refused("pair@test.bg")

    def test_unverified_social_email_never_matches(self):
        user = UserModel.objects.create_user(email="pair@test.bg", password="StrongPass123!")
        user.has_set_password = True
        user.save(update_fields=["has_set_password"])

        # No exception: an unverified social email must not influence linking.
        self.adapter.pre_social_login(self.request, self._sociallogin("pair@test.bg", verified=False))

    def test_passwordless_matching_account_is_not_refused(self):
        UserModel.objects.create_user(email="social@test.bg", password=None)

        # Social-created accounts have no password: the default allauth
        # flow (connect by verified email) proceeds.
        self.adapter.pre_social_login(self.request, self._sociallogin("social@test.bg"))
