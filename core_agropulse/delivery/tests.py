from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal

from core_agropulse.delivery.models import Delivery, RiderEarnings
from core_agropulse.accounts.models import (
    FarmerProfile,
    BuyerProfile,
    TransporterProfile,
)
from core_agropulse.orders.models import Order

User = get_user_model()


class DeliveryModelTests(TestCase):
    """Test cases for Delivery model"""

    def setUp(self):
        # Create farmer
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

        # Create buyer
        self.buyer_user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+0987654321",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Test Business",
            buyer_type="RESTAURANT",
            location="Test Location",
        )

        # Create transporter
        self.transporter_user = User.objects.create_user(
            full_name="Transporter Test",
            email="transporter@example.com",
            phone_number="+1122334455",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.transporter_profile = TransporterProfile.objects.create(
            user=self.transporter_user,
            vehicle_type="VAN",
            plate_number="ABC123",
            service_area="City Center",
        )

        # Create order with delivery type
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )

    def test_create_delivery(self):
        """Test creating a delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.assertEqual(delivery.order, self.order)
        self.assertEqual(delivery.transporter, self.transporter_profile)
        self.assertEqual(delivery.delivery_status, "PENDING")

    def test_delivery_status_choices(self):
        """Test delivery status choices"""
        delivery = Delivery.objects.create(  # noqa: F841
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        valid_statuses = [
            choice[0] for choice in Delivery._meta.get_field("delivery_status").choices
        ]
        self.assertIn("PENDING", valid_statuses)
        self.assertIn("PICKED_UP", valid_statuses)
        self.assertIn("IN_TRANSIT", valid_statuses)
        self.assertIn("DELIVERED", valid_statuses)

    def test_delivery_string_representation(self):
        """Test delivery __str__ method"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.assertIn(str(delivery.id), str(delivery))
        self.assertIn("PENDING", str(delivery))


class RiderEarningsModelTests(TestCase):
    """Test cases for RiderEarnings model"""

    def setUp(self):
        # Create farmer
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

        # Create buyer
        self.buyer_user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+0987654321",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Test Business",
            buyer_type="RESTAURANT",
            location="Test Location",
        )

        # Create transporter
        self.transporter_user = User.objects.create_user(
            full_name="Transporter Test",
            email="transporter@example.com",
            phone_number="+1122334455",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.transporter_profile = TransporterProfile.objects.create(
            user=self.transporter_user,
            vehicle_type="VAN",
            plate_number="ABC123",
            service_area="City Center",
        )

        # Create order and delivery
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("100.00"),
            delivery_type="DELIVERY",
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )

    def test_create_rider_earnings(self):
        """Test creating rider earnings"""
        earnings = RiderEarnings.objects.create(
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
        )
        self.assertEqual(earnings.transporter, self.transporter_profile)
        self.assertEqual(earnings.delivery, self.delivery)
        self.assertEqual(earnings.earnings_amount, Decimal("10.00"))
        self.assertEqual(earnings.payment_status, "PENDING")

    def test_earnings_payment_status_choices(self):
        """Test payment status choices"""
        earnings = RiderEarnings.objects.create(  # noqa: F841
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
        )
        valid_statuses = [
            choice[0]
            for choice in RiderEarnings._meta.get_field("payment_status").choices
        ]
        self.assertIn("PENDING", valid_statuses)
        self.assertIn("PAID", valid_statuses)
        self.assertIn("CANCELLED", valid_statuses)


class DeliveryAPITests(APITestCase):
    """Test cases for Delivery API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.delivery_url = "/api/deliveries/"

        # Create farmer
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

        # Create buyer
        self.buyer_user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+0987654321",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Test Business",
            buyer_type="RESTAURANT",
            location="Test Location",
        )

        # Create transporter
        self.transporter_user = User.objects.create_user(
            full_name="Transporter Test",
            email="transporter@example.com",
            phone_number="+1122334455",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.transporter_profile = TransporterProfile.objects.create(
            user=self.transporter_user,
            vehicle_type="VAN",
            plate_number="ABC123",
            service_area="City Center",
        )

        # Create order with delivery type
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("100.00"),
            delivery_type="DELIVERY",
        )

    def test_create_delivery(self):
        """Test creating a delivery"""
        self.client.force_authenticate(user=self.buyer_user)
        data = {
            "order": str(self.order.id),
            "transporter": str(self.transporter_profile.id),
            "delivery_address": "123 Main St",
        }
        response = self.client.post(self.delivery_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["delivery_status"], "PENDING")

    def test_list_deliveries(self):
        """Test listing deliveries"""
        Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.client.force_authenticate(user=self.transporter_user)
        response = self.client.get(self.delivery_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_delivery(self):
        """Test retrieving a delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.delivery_url}{delivery.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(delivery.id))

    def test_available_riders(self):
        """Test available riders endpoint"""
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.delivery_url}available_riders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            any(r["id"] == str(self.transporter_profile.id) for r in response.data)
        )

    def test_assign_rider(self):
        """Test assigning rider to delivery"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=None,
            delivery_address="123 Main St",
        )
        self.client.force_authenticate(user=self.buyer_user)
        url = f"{self.delivery_url}{delivery.id}/assign_rider/"
        data = {"transporter_id": str(self.transporter_profile.id)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            str(response.data["transporter"]), str(self.transporter_profile.id)
        )

    def test_pickup_confirmation(self):
        """Test pickup confirmation"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.delivery_url}{delivery.id}/pickup_confirmation/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["delivery_status"], "PICKED_UP")
        self.assertIsNotNone(response.data["picked_up_at"])

    def test_start_transit(self):
        """Test start transit"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        delivery.delivery_status = "PICKED_UP"
        delivery.save()

        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.delivery_url}{delivery.id}/start_transit/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["delivery_status"], "IN_TRANSIT")

    def test_delivery_confirmation(self):
        """Test delivery confirmation"""
        delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        delivery.delivery_status = "IN_TRANSIT"
        delivery.save()

        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.delivery_url}{delivery.id}/delivery_confirmation/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["delivery_status"], "DELIVERED")
        self.assertIsNotNone(response.data["delivered_at"])

        # Check that order status was updated
        self.order.refresh_from_db()
        self.assertEqual(self.order.order_status, "COMPLETED")

        # Check that earnings were created
        earnings = RiderEarnings.objects.filter(delivery=delivery)
        self.assertEqual(earnings.count(), 1)

    def test_my_deliveries(self):
        """Test my deliveries endpoint"""
        Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        self.client.force_authenticate(user=self.transporter_user)
        response = self.client.get(f"{self.delivery_url}my_deliveries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_pending_deliveries(self):
        """Test pending deliveries endpoint"""
        Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
        )
        response = self.client.get(f"{self.delivery_url}pending_deliveries/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class RiderEarningsAPITests(APITestCase):
    """Test cases for RiderEarnings API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.earnings_url = "/api/rider-earnings/"

        # Create farmer
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

        # Create buyer
        self.buyer_user = User.objects.create_user(
            full_name="Buyer Test",
            email="buyer@example.com",
            phone_number="+0987654321",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Test Business",
            buyer_type="RESTAURANT",
            location="Test Location",
        )

        # Create transporter
        self.transporter_user = User.objects.create_user(
            full_name="Transporter Test",
            email="transporter@example.com",
            phone_number="+1122334455",
            password="testpass123",
            role="TRANSPORTER",
        )
        self.transporter_profile = TransporterProfile.objects.create(
            user=self.transporter_user,
            vehicle_type="VAN",
            plate_number="ABC123",
            service_area="City Center",
        )

        # Create order and delivery
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("100.00"),
            delivery_type="DELIVERY",
        )
        self.delivery = Delivery.objects.create(
            order=self.order,
            transporter=self.transporter_profile,
            delivery_address="123 Main St",
            delivery_status="DELIVERED",
        )

    def test_list_earnings(self):
        """Test listing earnings"""
        RiderEarnings.objects.create(
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user=self.transporter_user)
        response = self.client.get(self.earnings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_earnings(self):
        """Test retrieving earnings detail"""
        earnings = RiderEarnings.objects.create(
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.earnings_url}{earnings.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(earnings.id))

    def test_my_earnings(self):
        """Test my earnings endpoint"""
        RiderEarnings.objects.create(
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
        )
        self.client.force_authenticate(user=self.transporter_user)
        response = self.client.get(f"{self.earnings_url}my_earnings/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total_earned", response.data)
        self.assertIn("total_paid", response.data)
        self.assertIn("total_pending", response.data)
        self.assertIn("completed_deliveries", response.data)

    def test_mark_as_paid(self):
        """Test marking earnings as paid"""
        earnings = RiderEarnings.objects.create(
            transporter=self.transporter_profile,
            delivery=self.delivery,
            earnings_amount=Decimal("10.00"),
            payment_status="PENDING",
        )
        self.client.force_authenticate(user=self.transporter_user)
        url = f"{self.earnings_url}{earnings.id}/mark_as_paid/"
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["payment_status"], "PAID")
        self.assertIsNotNone(response.data["paid_at"])
