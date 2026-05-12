from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date

from core_agropulse.produce.models import Produce
from core_agropulse.accounts.models import FarmerProfile

User = get_user_model()


class ProduceModelTests(TestCase):
    """Test cases for Produce model"""

    def setUp(self):
        # Create user and farmer profile
        self.user = User.objects.create_user(
            full_name="Farmer John",
            email="farmer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="SELLER",
        )
        self.farmer = FarmerProfile.objects.create(
            user=self.user,
            farm_name="Green Farm",
            farm_location="California",
        )

        self.produce_data = {
            "produce_name": "Tomato",
            "category": "VEGETABLES",
            "unit_price": 2.50,
            "quantity_available": 100,
            "harvest_date": date(2026, 5, 10),
        }

    def test_create_produce(self):
        """Test creating a produce"""
        produce = Produce.objects.create(farmer=self.farmer, **self.produce_data)
        self.assertEqual(produce.produce_name, "Tomato")
        self.assertEqual(produce.category, "VEGETABLES")
        self.assertEqual(produce.availability_status, "AVAILABLE")

    def test_produce_default_availability(self):
        """Test produce has default availability status"""
        produce = Produce.objects.create(farmer=self.farmer, **self.produce_data)
        self.assertEqual(produce.availability_status, "AVAILABLE")

    def test_produce_string_representation(self):
        """Test produce __str__ method"""
        produce = Produce.objects.create(farmer=self.farmer, **self.produce_data)
        self.assertEqual(str(produce), "Tomato - Green Farm (AVAILABLE)")

    def test_produce_categories(self):
        """Test all valid produce categories"""
        for category in ["VEGETABLES", "FRUITS", "GRAINS", "DAIRY", "MEAT", "OTHER"]:
            data = self.produce_data.copy()
            data["category"] = category
            produce = Produce.objects.create(farmer=self.farmer, **data)
            self.assertEqual(produce.category, category)


class ProduceAPITests(APITestCase):
    """Test cases for Produce API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.produce_url = "/api/produces/"

        # Create farmer user
        self.farmer_user = User.objects.create_user(
            full_name="Farmer Test",
            email="farmer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="SELLER",
        )
        self.farmer_profile = FarmerProfile.objects.create(
            user=self.farmer_user,
            farm_name="Test Farm",
            farm_location="Test Location",
        )

        # Create buyer user (for non-farmer permissions test)
        self.buyer_user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="BUYER",
        )

        self.produce_data = {
            "farmer": self.farmer_profile.id,
            "produce_name": "Tomato",
            "category": "VEGETABLES",
            "unit_price": "2.50",
            "quantity_available": 100,
            "harvest_date": "2026-05-10",
        }

        # Data for direct model creation (without farmer field)
        self.model_produce_data = {
            "produce_name": "Tomato",
            "category": "VEGETABLES",
            "unit_price": 2.50,
            "quantity_available": 100,
            "harvest_date": date(2026, 5, 10),
        }

    def test_list_produces_unauthenticated(self):
        """Test listing produces without authentication"""
        response = self.client.get(self.produce_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_produce_authenticated(self):
        """Test creating a produce with authenticated farmer"""
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.post(self.produce_url, self.produce_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["produce_name"], "Tomato")

    def test_create_produce_without_farmer_profile(self):
        """Test creating produce without farmer profile"""
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.post(self.produce_url, self.produce_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_produce_unauthenticated(self):
        """Test creating produce without authentication"""
        response = self.client.post(self.produce_url, self.produce_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_produce(self):
        """Test retrieving a produce"""
        produce = Produce.objects.create(
            farmer=self.farmer_profile, **self.model_produce_data
        )
        url = f"{self.produce_url}{produce.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["produce_name"], "Tomato")

    def test_update_produce(self):
        """Test updating a produce"""
        produce = Produce.objects.create(
            farmer=self.farmer_profile, **self.model_produce_data
        )
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.produce_url}{produce.id}/"
        updated_data = {
            "produce_name": "Red Tomato",
            "unit_price": "3.50",
        }
        response = self.client.patch(url, updated_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["produce_name"], "Red Tomato")

    def test_delete_produce(self):
        """Test deleting a produce"""
        produce = Produce.objects.create(
            farmer=self.farmer_profile, **self.model_produce_data
        )
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.produce_url}{produce.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_my_produces_endpoint(self):
        """Test getting user's own produces"""
        Produce.objects.create(farmer=self.farmer_profile, **self.model_produce_data)
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(f"{self.produce_url}my_produces/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_available_produces_endpoint(self):
        """Test getting available produces"""
        Produce.objects.create(farmer=self.farmer_profile, **self.model_produce_data)
        response = self.client.get(f"{self.produce_url}available/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_by_category_endpoint(self):
        """Test filtering produces by category"""
        Produce.objects.create(farmer=self.farmer_profile, **self.model_produce_data)
        response = self.client.get(
            f"{self.produce_url}by_category/?category=VEGETABLES"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_stock_endpoint(self):
        """Test updating stock via custom endpoint"""
        produce = Produce.objects.create(
            farmer=self.farmer_profile, **self.model_produce_data
        )
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.produce_url}{produce.id}/update_stock/"
        response = self.client.patch(url, {"quantity_available": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["availability_status"], "LOW_STOCK")

    def test_update_stock_sold_out(self):
        """Test stock update reflects sold out status"""
        produce = Produce.objects.create(
            farmer=self.farmer_profile, **self.model_produce_data
        )
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.produce_url}{produce.id}/update_stock/"
        response = self.client.patch(url, {"quantity_available": 0}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["availability_status"], "SOLD_OUT")

    def test_filter_by_category(self):
        """Test filtering produces by category via query parameter"""
        data = self.model_produce_data.copy()
        data["category"] = "FRUITS"
        Produce.objects.create(farmer=self.farmer_profile, **data)
        Produce.objects.create(farmer=self.farmer_profile, **self.model_produce_data)

        response = self.client.get(f"{self.produce_url}?category=FRUITS")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_by_produce_name(self):
        """Test searching produces by name"""
        Produce.objects.create(farmer=self.farmer_profile, **self.model_produce_data)
        response = self.client.get(f"{self.produce_url}?search=Tomato")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
