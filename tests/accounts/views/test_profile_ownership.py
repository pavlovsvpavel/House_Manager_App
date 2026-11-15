from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from house_manager.accounts.models import Profile

UserModel = get_user_model()


class ProfileOwnershipTests(TestCase):
    """Profile pages are keyed by the user's pk (#13): the owner reaches
    them, a foreign pk is rejected with 403, and deleting the profile
    removes the user (cascading to the Profile) without crashing."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = UserModel.objects.create_user(
            email="alice@test.bg", password="StrongPass123!")
        cls.bob = UserModel.objects.create_user(
            email="bob@test.bg", password="StrongPass123!")

    def profile_urls(self, user):
        pk = user.pk
        return [
            reverse("details_profile", kwargs={"pk": pk}),
            reverse("edit_profile", kwargs={"pk": pk}),
            reverse("delete_profile", kwargs={"pk": pk}),
            reverse("change_password", kwargs={"pk": pk}),
            reverse("set_password", kwargs={"pk": pk}),
        ]

    def test_owner_reaches_own_profile_pages(self):
        self.client.force_login(self.alice)

        for url in self.profile_urls(self.alice):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_foreign_profile_pk_is_rejected_with_403(self):
        self.client.force_login(self.alice)

        for url in self.profile_urls(self.bob):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

    def test_delete_removes_user_and_profile_and_logs_out(self):
        self.client.force_login(self.alice)

        response = self.client.post(
            reverse("delete_profile", kwargs={"pk": self.alice.pk}))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            UserModel.objects.filter(pk=self.alice.pk).exists())
        self.assertFalse(
            Profile.objects.filter(user_id=self.alice.pk).exists())
        # The session was terminated with the account.
        self.assertNotIn("_auth_user_id", self.client.session)
