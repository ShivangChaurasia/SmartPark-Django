from django.test import TestCase
from accounts.models import User


class AccountsModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='securepassword123',
            role='user'
        )

    def test_user_creation_and_hashing(self):
        self.assertEqual(self.user.username, 'johndoe')
        self.assertTrue(self.user.check_password('securepassword123'))
        self.assertFalse(self.user.check_password('wrongpassword'))

    def test_host_verification(self):
        self.assertFalse(self.user.is_verified_host())
        self.user.role = 'host'
        self.user.kyc_status = 'verified'
        self.user.save()
        self.assertTrue(self.user.is_verified_host())
