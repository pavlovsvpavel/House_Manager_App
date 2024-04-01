from django.contrib.auth import get_user_model
from django.core import exceptions
from django.test import TestCase

from house_manager.accounts.models import Profile

UserModel = get_user_model()


class ProfileTests(TestCase):
    def test_profile__when_user_is_created__expect_profile_creation(self):
        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        user = UserModel.objects.create_user(**user_data)
        profile = Profile.objects.filter(user_id=user.id).first()

        self.assertEqual(user.id, profile.user.id)

    def test_profile__add_phone_number_with_alphabetic_characters__expect_validation_error(self):
        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        user = UserModel.objects.create_user(**user_data)
        profile = Profile.objects.filter(user_id=user.id).first()

        with self.assertRaises(exceptions.ValidationError) as ve:
            profile.phone_number = 'd88812345d'
            profile.full_clean()

        exception = ve.exception
        phone_number_exception = str(exception.error_dict["phone_number"][0])

        self.assertEqual("['Phone number should contains only digits']", phone_number_exception)

    def test_profile__add_profile_picture_size_exceed_limit__expect_validation_error(self):
        user_data = {
            'email': 'admin@admin.bg',
            "password": "123456",
        }

        user = UserModel.objects.create_user(**user_data)
        profile = Profile.objects.filter(user_id=user.id).first()

        class MockFile:
            def __init__(self, size):
                self.size = size

        mock_file = MockFile(size=2 * 1024 * 1024)

        with self.assertRaises(exceptions.ValidationError) as ve:
            profile.profile_picture = mock_file
            profile.full_clean()

        exception = ve.exception
        profile_picture_exception = str(exception.error_dict["profile_picture"][0])

        self.assertEqual("['The maximum file size should not exceed 1MB']", profile_picture_exception)