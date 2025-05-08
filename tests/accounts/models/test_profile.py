from django.contrib.auth import get_user_model
from django.core import exceptions
from django.test import TestCase

from house_manager.accounts.models import Profile
from house_manager.accounts.validators import validate_image_file, validate_profile_picture_size

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

    def test_profile__upload_unsupported_file_type__expect_validation_error(self):
        file_data = b'PDF Content'

        class FakeFile:
            def __init__(self, name, size, content_type):
                self.name = name
                self.size = size
                self.content_type = content_type

        fake_file = FakeFile(name='test_file.pdf', size=len(file_data), content_type='application/pdf')

        with self.assertRaises(exceptions.ValidationError) as ve:
            validate_image_file(fake_file)

        exception = ve.exception

        self.assertEqual(exception.message, 'Unsupported file type. Please upload an image file (.jpg, .jpeg, .png, .gif)')

    def test_profile__upload_image_bigger_than_size_limit__expect_validation_error(self):
        file_data = b'x' * (3 * 1024 * 1024 + 1)

        class FakeFile:
            def __init__(self, name, size, content_type):
                self.name = name
                self.size = size
                self.content_type = content_type

        fake_file = FakeFile(name='test_file.jpg', size=len(file_data), content_type='image/jpeg')

        with self.assertRaises(exceptions.ValidationError) as ve:
            validate_profile_picture_size(fake_file)

        exception = ve.exception

        self.assertEqual(exception.message, 'The maximum file size should not exceed 3MB')
