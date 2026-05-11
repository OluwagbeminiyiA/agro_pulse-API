from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from core_agropulse.accounts.models import (
    FarmerProfile,
    BuyerProfile,
    TransporterProfile,
)

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for User model"""

    def setUp(self):
        self.user_data = {
            "full_name": "John Doe",
            "email": "john@example.com",
            "phone_number": "+1234567890",
            "password": "testpass123",
            "role": "BUYER",
        }

    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.full_name, "John Doe")
        self.assertEqual(user.role, "BUYER")
        self.assertTrue(user.is_active)

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
            full_name="Admin User",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_email_unique(self):
        """Test that email is unique"""
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(**self.user_data)

    def test_user_password_hashing(self):
        """Test password is properly hashed"""
        user = User.objects.create_user(**self.user_data)
        self.assertNotEqual(user.password, "testpass123")
        self.assertTrue(user.check_password("testpass123"))

    def test_user_string_representation(self):
        """Test user __str__ method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), "John Doe (BUYER)")


class FarmerProfileModelTests(TestCase):
    """Test cases for FarmerProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            full_name="Farmer John",
            email="farmer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="SELLER",
        )
        self.farmer_data = {
            "farm_name": "Green Acres Farm",
            "farm_location": "California",
            "trust_score": 4.5,
        }

    def test_create_farmer_profile(self):
        """Test creating farmer profile"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        self.assertEqual(farmer.farm_name, "Green Acres Farm")
        self.assertEqual(farmer.trust_score, 4.5)
        self.assertEqual(farmer.user, self.user)

    def test_farmer_profile_string_representation(self):
        """Test farmer profile __str__ method"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        self.assertEqual(str(farmer), "Green Acres Farm - Farmer John")

    def test_farmer_profile_one_to_one_relationship(self):
        """Test one-to-one relationship with User"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        self.assertEqual(farmer.user.email, "farmer@example.com")


class BuyerProfileModelTests(TestCase):
    """Test cases for BuyerProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            full_name="Buyer John",
            email="buyer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_data = {
            "business_name": "Fresh Foods Store",
            "buyer_type": "WHOLESALER",
            "location": "New York",
        }

    def test_create_buyer_profile(self):
        """Test creating buyer profile"""
        buyer = BuyerProfile.objects.create(user=self.user, **self.buyer_data)
        self.assertEqual(buyer.business_name, "Fresh Foods Store")
        self.assertEqual(buyer.buyer_type, "WHOLESALER")

    def test_buyer_profile_valid_buyer_types(self):
        """Test all valid buyer types"""
        for idx, buyer_type in enumerate(["INDIVIDUAL", "RESTAURANT", "WHOLESALER"]):
            user = User.objects.create_user(
                full_name=f"Test Buyer {idx}",
                email=f"buyer{idx}@example.com",
                phone_number="+1234567890",
                password="testpass123",
                role="BUYER",
            )
            buyer_data = self.buyer_data.copy()
            buyer_data["buyer_type"] = buyer_type
            buyer = BuyerProfile.objects.create(user=user, **buyer_data)
            self.assertEqual(buyer.buyer_type, buyer_type)


class TransporterProfileModelTests(TestCase):
    """Test cases for TransporterProfile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            full_name="Transporter John",
            email="transporter@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.transporter_data = {
            "vehicle_type": "Truck",
            "plate_number": "ABC123XYZ",
            "service_area": "California",
        }

    def test_create_transporter_profile(self):
        """Test creating transporter profile"""
        transporter = TransporterProfile.objects.create(
            user=self.user, **self.transporter_data
        )
        self.assertEqual(transporter.vehicle_type, "Truck")
        self.assertEqual(transporter.plate_number, "ABC123XYZ")

    def test_transporter_profile_string_representation(self):
        """Test transporter profile __str__ method"""
        transporter = TransporterProfile.objects.create(
            user=self.user, **self.transporter_data
        )
        self.assertEqual(str(transporter), "ABC123XYZ - Transporter John")


class UserAPITests(APITestCase):
    """Test cases for User API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = "/api/users/register/"
        self.user_list_url = "/api/users/"
        self.me_url = "/api/users/me/"

        self.user_data = {
            "full_name": "Test User",
            "email": "testuser@example.com",
            "phone_number": "+1234567890",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "role": "BUYER",
        }

    def test_user_registration(self):
        """Test user registration endpoint"""
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "testuser@example.com")
        self.assertIn("id", response.data)

    def test_user_registration_password_mismatch(self):
        """Test registration with mismatched passwords"""
        data = self.user_data.copy()
        data["password_confirm"] = "differentpass"
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email"""
        self.client.post(self.register_url, self.user_data, format="json")
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_current_user(self):
        """Test getting current user profile"""
        self.client.post(self.register_url, self.user_data, format="json")
        user = User.objects.get(email="testuser@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "testuser@example.com")

    def test_list_users(self):
        """Test listing users"""
        self.client.post(self.register_url, self.user_data, format="json")
        user = User.objects.get(email="testuser@example.com")
        self.client.force_authenticate(user=user)

        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_user_login(self):
        """Test user login endpoint"""
        # First register a user
        self.client.post(self.register_url, self.user_data, format="json")

        # Then login
        login_url = "/api/users/login/"
        login_data = {
            "email": "testuser@example.com",
            "password": "testpass123",
        }
        response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "testuser@example.com")

    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_url = "/api/users/login/"
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FarmerProfileAPITests(APITestCase):
    """Test cases for FarmerProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.farmer_url = "/api/farmers/"

        # Create a user
        self.user = User.objects.create_user(
            full_name="Farmer Test",
            email="farmer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="BUYER",
        )
        self.client.force_authenticate(user=self.user)

        self.farmer_data = {
            "farm_name": "Test Farm",
            "farm_location": "Test Location",
            "trust_score": 3.5,
        }

    def test_create_farmer_profile(self):
        """Test creating farmer profile via API"""
        response = self.client.post(self.farmer_url, self.farmer_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["farm_name"], "Test Farm")

    def test_list_farmer_profiles(self):
        """Test listing farmer profiles"""
        FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        response = self.client.get(self.farmer_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_farmer_profile(self):
        """Test retrieving farmer profile"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        url = f"{self.farmer_url}{farmer.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["farm_name"], "Test Farm")

    def test_update_farmer_profile(self):
        """Test updating farmer profile"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        url = f"{self.farmer_url}{farmer.id}/"
        updated_data = self.farmer_data.copy()
        updated_data["farm_name"] = "Updated Farm"
        response = self.client.patch(url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["farm_name"], "Updated Farm")

    def test_delete_farmer_profile(self):
        """Test deleting farmer profile"""
        farmer = FarmerProfile.objects.create(user=self.user, **self.farmer_data)
        url = f"{self.farmer_url}{farmer.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FarmerProfile.objects.filter(id=farmer.id).exists())


class BuyerProfileAPITests(APITestCase):
    """Test cases for BuyerProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.buyer_url = "/api/buyers/"

        # Create a user
        self.user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="BUYER",
        )
        self.client.force_authenticate(user=self.user)

        self.buyer_data = {
            "business_name": "Test Business",
            "buyer_type": "RESTAURANT",
            "location": "Test Location",
        }

    def test_create_buyer_profile(self):
        """Test creating buyer profile via API"""
        response = self.client.post(self.buyer_url, self.buyer_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["business_name"], "Test Business")

    def test_list_buyer_profiles(self):
        """Test listing buyer profiles"""
        BuyerProfile.objects.create(user=self.user, **self.buyer_data)
        response = self.client.get(self.buyer_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_buyer_profile_types(self):
        """Test different buyer types"""
        for idx, buyer_type in enumerate(["INDIVIDUAL", "RESTAURANT", "WHOLESALER"]):
            # Create new user for each buyer type
            user = User.objects.create_user(
                full_name=f"Buyer {idx}",
                email=f"buyer{idx}@example.com",
                phone_number="+1234567890",
                password="testpass123",
                role="BUYER",
            )
            self.client.force_authenticate(user=user)

            data = {
                "business_name": f"Test Business {buyer_type}",
                "buyer_type": buyer_type,
                "location": "Test Location",
            }
            response = self.client.post(self.buyer_url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TransporterProfileAPITests(APITestCase):
    """Test cases for TransporterProfile API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.transporter_url = "/api/transporters/"

        # Create a user
        self.user = User.objects.create_user(
            full_name="Transporter Test",
            email="transporter@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.client.force_authenticate(user=self.user)

        self.transporter_data = {
            "vehicle_type": "Van",
            "plate_number": "XYZ789ABC",
            "service_area": "Test Area",
        }

    def test_create_transporter_profile(self):
        """Test creating transporter profile via API"""
        response = self.client.post(
            self.transporter_url, self.transporter_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["vehicle_type"], "Van")

    def test_list_transporter_profiles(self):
        """Test listing transporter profiles"""
        TransporterProfile.objects.create(user=self.user, **self.transporter_data)
        response = self.client.get(self.transporter_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_transporter_profile(self):
        """Test retrieving transporter profile"""
        transporter = TransporterProfile.objects.create(
            user=self.user, **self.transporter_data
        )
        url = f"{self.transporter_url}{transporter.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["plate_number"], "XYZ789ABC")
