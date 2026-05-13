from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta

from core_agropulse.subscriptions.models import (
    Subscription,
    SubscriptionOrder,
    SubscriptionPayment,
)
from core_agropulse.accounts.models import (
    FarmerProfile,
    BuyerProfile,
)
from core_agropulse.produce.models import Produce

User = get_user_model()


class SubscriptionModelTests(TestCase):
    """Test cases for Subscription model"""

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

        # Create produce
        self.produce = Produce.objects.create(
            farmer=self.farmer_profile,
            produce_name="Tomatoes",
            category="VEGETABLES",
            unit_price=500.00,
            quantity_available=100,
            harvest_date=date.today(),
        )

    def test_create_subscription(self):
        """Test creating a subscription"""
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        self.assertEqual(subscription.buyer, self.buyer_profile)
        self.assertEqual(subscription.frequency, "WEEKLY")
        self.assertTrue(subscription.active)

    def test_subscription_pause(self):
        """Test pausing a subscription"""
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        subscription.pause()
        self.assertEqual(subscription.status, "PAUSED")
        self.assertFalse(subscription.active)

    def test_subscription_resume(self):
        """Test resuming a subscription"""
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        subscription.pause()
        subscription.resume()
        self.assertEqual(subscription.status, "ACTIVE")
        self.assertTrue(subscription.active)

    def test_subscription_cancel(self):
        """Test cancelling a subscription"""
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        subscription.cancel()
        self.assertEqual(subscription.status, "CANCELLED")
        self.assertFalse(subscription.active)
        self.assertIsNotNone(subscription.subscription_end_date)

    def test_calculate_next_order_date_daily(self):
        """Test calculating next order date for daily frequency"""
        today = date.today()
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="DAILY",
            expected_quantity=10,
            next_expected_order_date=today,
        )
        next_date = subscription.calculate_next_order_date()
        self.assertEqual(next_date, today + timedelta(days=1))

    def test_calculate_next_order_date_weekly(self):
        """Test calculating next order date for weekly frequency"""
        today = date.today()
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=today,
        )
        next_date = subscription.calculate_next_order_date()
        self.assertEqual(next_date, today + timedelta(weeks=1))

    def test_subscription_unique_constraint(self):
        """Test that buyer-farmer-produce combination is unique"""
        Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        with self.assertRaises(Exception):
            Subscription.objects.create(
                buyer=self.buyer_profile,
                farmer=self.farmer_profile,
                produce=self.produce,
                frequency="DAILY",
                expected_quantity=5,
                next_expected_order_date=date.today(),
            )


class SubscriptionOrderModelTests(TestCase):
    """Test cases for SubscriptionOrder model"""

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

        # Create produce
        self.produce = Produce.objects.create(
            farmer=self.farmer_profile,
            produce_name="Tomatoes",
            category="VEGETABLES",
            unit_price=500.00,
            quantity_available=100,
            harvest_date=date.today(),
        )

        # Create subscription
        self.subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )

    def test_create_subscription_order(self):
        """Test creating a subscription order"""
        order = SubscriptionOrder.objects.create(
            subscription=self.subscription,
            quantity=10,
            unit_price=500.00,
            total_amount=5000.00,
            scheduled_date=date.today(),
        )
        self.assertEqual(order.subscription, self.subscription)
        self.assertEqual(order.order_status, "PENDING")

    def test_subscription_order_total_calculation(self):
        """Test that total amount is correctly set"""
        order = SubscriptionOrder.objects.create(
            subscription=self.subscription,
            quantity=10,
            unit_price=500.00,
            total_amount=5000.00,
            scheduled_date=date.today(),
        )
        self.assertEqual(order.total_amount, 5000.00)


class SubscriptionPaymentModelTests(TestCase):
    """Test cases for SubscriptionPayment model"""

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

        # Create produce
        self.produce = Produce.objects.create(
            farmer=self.farmer_profile,
            produce_name="Tomatoes",
            category="VEGETABLES",
            unit_price=500.00,
            quantity_available=100,
            harvest_date=date.today(),
        )

        # Create subscription
        self.subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )

        # Create subscription order
        self.order = SubscriptionOrder.objects.create(
            subscription=self.subscription,
            quantity=10,
            unit_price=500.00,
            total_amount=5000.00,
            scheduled_date=date.today(),
        )

    def test_create_subscription_payment(self):
        """Test creating a subscription payment"""
        payment = SubscriptionPayment.objects.create(
            subscription_order=self.order,
            amount=5000.00,
            payment_status="PENDING",
        )
        self.assertEqual(payment.subscription_order, self.order)
        self.assertEqual(payment.payment_status, "PENDING")

    def test_subscription_payment_default_method(self):
        """Test that payment method defaults to 'auto'"""
        payment = SubscriptionPayment.objects.create(
            subscription_order=self.order,
            amount=5000.00,
        )
        self.assertEqual(payment.payment_method, "auto")


class SubscriptionAPITests(TestCase):
    """Test cases for Subscription API endpoints"""

    def setUp(self):
        self.client = APIClient()

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

        # Create produce
        self.produce = Produce.objects.create(
            farmer=self.farmer_profile,
            produce_name="Tomatoes",
            category="VEGETABLES",
            unit_price=500.00,
            quantity_available=100,
            harvest_date=date.today(),
        )

        # Login buyer
        self.client.force_authenticate(user=self.buyer_user)
        self.subscription_url = "/api/subscriptions/"

    def test_list_subscriptions_unauthenticated(self):
        """Test listing subscriptions without authentication"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.subscription_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_subscriptions_authenticated(self):
        """Test listing subscriptions with authentication"""
        response = self.client.get(self.subscription_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_subscription(self):
        """Test creating a subscription"""
        data = {
            "buyer": str(self.buyer_profile.id),
            "farmer": str(self.farmer_profile.id),
            "produce": str(self.produce.id),
            "frequency": "WEEKLY",
            "expected_quantity": 10,
            "next_expected_order_date": (date.today() + timedelta(days=7)).isoformat(),
        }
        response = self.client.post(self.subscription_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_pause_subscription(self):
        """Test pausing a subscription"""
        subscription = Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        response = self.client.post(f"{self.subscription_url}{subscription.id}/pause/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, "PAUSED")

    def test_my_subscriptions(self):
        """Test getting user's subscriptions"""
        Subscription.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            produce=self.produce,
            frequency="WEEKLY",
            expected_quantity=10,
            next_expected_order_date=date.today() + timedelta(days=7),
        )
        response = self.client.get(f"{self.subscription_url}my_subscriptions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
