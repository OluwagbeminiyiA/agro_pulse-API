from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal

from core_agropulse.payments.models import Payment, EscrowAccount, PaymentSplit, Payout
from core_agropulse.accounts.models import (
    FarmerProfile,
    BuyerProfile,
)
from core_agropulse.orders.models import Order

User = get_user_model()


class PaymentModelTests(TestCase):
    """Test cases for Payment model"""

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

        # Create order
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )

    def test_create_payment(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total,
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, Decimal("1000.00"))
        self.assertEqual(payment.payment_status, "PENDING")

    def test_payment_status_choices(self):
        """Test payment status choices"""
        payment = Payment.objects.create(
            order=self.order,
            amount=self.order.total,
        )
        valid_statuses = [
            choice[0] for choice in Payment._meta.get_field("payment_status").choices
        ]
        self.assertIn("PENDING", valid_statuses)
        self.assertIn("SUCCESS", valid_statuses)
        self.assertIn("FAILED", valid_statuses)
        self.assertIn("REFUNDED", valid_statuses)


class EscrowAccountModelTests(TestCase):
    """Test cases for EscrowAccount model"""

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

        # Create order and payment
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )

    def test_create_escrow(self):
        """Test creating an escrow account"""
        escrow = EscrowAccount.objects.create(
            payment=self.payment,
            farmer=self.farmer_profile,
            amount_held=Decimal("1000.00"),
        )
        self.assertEqual(escrow.payment, self.payment)
        self.assertEqual(escrow.amount_held, Decimal("1000.00"))
        self.assertEqual(escrow.release_status, "HELD")


class PaymentSplitModelTests(TestCase):
    """Test cases for PaymentSplit model"""

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

        # Create order and payment
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )

    def test_create_payment_split(self):
        """Test creating payment split"""
        split = PaymentSplit.objects.create(
            payment=self.payment,
            farmer_amount=Decimal("800.00"),
            rider_amount=Decimal("100.00"),
            platform_fee=Decimal("100.00"),
        )
        self.assertEqual(split.farmer_amount, Decimal("800.00"))
        self.assertEqual(split.rider_amount, Decimal("100.00"))
        self.assertEqual(split.platform_fee, Decimal("100.00"))

    def test_payment_split_totals(self):
        """Test that split amounts sum correctly"""
        split = PaymentSplit.objects.create(
            payment=self.payment,
            farmer_amount=Decimal("800.00"),
            rider_amount=Decimal("100.00"),
            platform_fee=Decimal("100.00"),
        )
        total_split = split.farmer_amount + split.rider_amount + split.platform_fee
        self.assertEqual(total_split, self.payment.amount)


class PayoutModelTests(TestCase):
    """Test cases for Payout model"""

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

        # Create order and payment
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )

    def test_create_payout(self):
        """Test creating a payout"""
        payout = Payout.objects.create(
            payment=self.payment,
            farmer=self.farmer_profile,
            payout_type="FARMER",
            amount=Decimal("800.00"),
        )
        self.assertEqual(payout.payout_type, "FARMER")
        self.assertEqual(payout.amount, Decimal("800.00"))
        self.assertEqual(payout.payout_status, "PENDING")

    def test_payout_status_choices(self):
        """Test payout status choices"""
        payout = Payout.objects.create(
            payment=self.payment,
            farmer=self.farmer_profile,
            payout_type="FARMER",
            amount=Decimal("800.00"),
        )
        valid_statuses = [
            choice[0] for choice in Payout._meta.get_field("payout_status").choices
        ]
        self.assertIn("PENDING", valid_statuses)
        self.assertIn("PROCESSING", valid_statuses)
        self.assertIn("COMPLETED", valid_statuses)
        self.assertIn("FAILED", valid_statuses)


class PaymentAPITests(APITestCase):
    """Test cases for Payment API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.payment_url = "/api/payments/"

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

        # Create order
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )

    def test_list_payments_unauthenticated(self):
        """Test listing payments without authentication"""
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_payments_authenticated(self):
        """Test listing payments with authentication"""
        Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(self.payment_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_pending_payments(self):
        """Test getting pending payments"""
        Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.payment_url}pending_payments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_my_payments(self):
        """Test getting current user's payments"""
        Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.payment_url}my_payments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class EscrowAccountAPITests(APITestCase):
    """Test cases for EscrowAccount API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.escrow_url = "/api/escrow/"

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

        # Create order, payment, and escrow
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )
        self.escrow = EscrowAccount.objects.create(
            payment=self.payment,
            farmer=self.farmer_profile,
            amount_held=Decimal("1000.00"),
        )

    def test_list_escrow_accounts(self):
        """Test listing escrow accounts"""
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(self.escrow_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_escrow_account(self):
        """Test retrieving escrow account details"""
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.escrow_url}{self.escrow.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["id"]), str(self.escrow.id))

    def test_held_funds(self):
        """Test getting held escrowed funds"""
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(f"{self.escrow_url}held_funds/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class PayoutAPITests(APITestCase):
    """Test cases for Payout API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.payout_url = "/api/payouts/"

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

        # Create order, payment, and payout
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=Decimal("1000.00"),
            delivery_type="DELIVERY",
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal("1000.00"),
        )
        self.payout = Payout.objects.create(
            payment=self.payment,
            farmer=self.farmer_profile,
            payout_type="FARMER",
            amount=Decimal("800.00"),
        )

    def test_list_payouts(self):
        """Test listing payouts"""
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_my_payouts(self):
        """Test getting user's payouts"""
        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(f"{self.payout_url}my_payouts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_mark_payout_completed(self):
        """Test marking payout as completed"""
        # Create payment split for this test
        PaymentSplit.objects.create(
            payment=self.payment,
            farmer_amount=Decimal("800.00"),
            rider_amount=Decimal("100.00"),
            platform_fee=Decimal("100.00"),
        )

        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.payout_url}{self.payout.id}/mark_completed/"
        data = {"bank_reference": "REF123456"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["payout_status"], "COMPLETED")
        self.assertEqual(response.data["bank_reference"], "REF123456")

    def test_pending_farmer_payouts_admin(self):
        """Test admin can view pending farmer payouts"""
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            full_name="Admin User",
        )
        self.client.force_authenticate(user=admin_user)
        response = self.client.get(f"{self.payout_url}pending_farmer_payouts/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
