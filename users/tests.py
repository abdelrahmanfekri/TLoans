from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


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


class UserViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            "email": "test@gmail.com",
            "password": "testpass123",
            "phone_number": "+211052858386",
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_register_view(self):
        url = reverse("users:register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        new_user_data = {
            "email": "newuser@gmail.com",
            "phone_number": "+221002857386",
            "password1": "newpass123",
            "password2": "newpass123",
        }
        response = self.client.post(url, data=new_user_data)
        self.assertRedirects(response, reverse("home"))
        self.assertTrue(User.objects.filter(email="newuser@gmail.com").exists())

    def test_login_logout_view(self):
        login_url = reverse("users:login")
        login_data = {
            "username": self.user_data["email"],
            "password": self.user_data["password"],
        }
        response = self.client.post(login_url, data=login_data)
        self.assertRedirects(response, reverse("home"))

        protected_url = reverse("users:protected")
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "You are logged in")

        logout_url = reverse("users:logout")
        response = self.client.get(logout_url)
        self.assertRedirects(response, reverse("home"))

        response = self.client.get(protected_url)
        self.assertRedirects(response, f"{reverse('users:login')}?next={protected_url}")
