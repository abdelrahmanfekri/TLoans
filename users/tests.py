from django.test import TestCase
from django.contrib.auth import get_user_model


class CustomUserTest(TestCase):

    def test_create_user(self):
        UserModel = get_user_model()
        user = UserModel.objects.create_user(
            email="test@gmail.com", phone_number="+201002857386", password="password1"
        )
        self.assertEqual(user.email, "test@gmail.com")
        self.assertEqual(user.phone_number, "+201002857386")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIsNone(user.username)

    def test_create_superuser(self):
        UserModel = get_user_model()
        admin_user = UserModel.objects.create_superuser(
            email="admin@gmail.com", phone_number="+201002857386", password="password1"
        )
        self.assertEqual(admin_user.email, "admin@gmail.com")
        self.assertEqual(admin_user.phone_number, "+201002857386")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertIsNone(admin_user.username)
