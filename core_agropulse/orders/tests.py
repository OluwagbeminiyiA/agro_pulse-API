from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from datetime import date

from core_agropulse.orders.models import Order, OrderItem
from core_agropulse.accounts.models import FarmerProfile, BuyerProfile
from core_agropulse.produce.models import Produce

User = get_user_model()


class OrderModelTests(TestCase):
    """Test cases for Order model"""

    def setUp(self):
        # Create farmer user and profile
        self.farmer_user = User.objects.create_user(
            full_name="Farmer John",
            email="farmer@example.com",
            phone_number="+1234567890",
            password="testpass123",
            role="SELLER",
        )
        self.farmer_profile = FarmerProfile.objects.create(
            user=self.farmer_user,
            farm_name="Green Farm",
            farm_location="California",
        )

        # Create buyer user and profile
        self.buyer_user = User.objects.create_user(
            full_name="Buyer John",
            email="buyer@example.com",
            phone_number="+0987654321",
            password="testpass123",
            role="BUYER",
        )
        self.buyer_profile = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Fresh Market",
            buyer_type="RESTAURANT",
            location="New York",
        )

        self.order_data = {
            "buyer": self.buyer_profile,
            "farmer": self.farmer_profile,
            "total": 150.50,
            "delivery_type": "DELIVERY",
        }

    def test_create_order(self):
        """Test creating an order"""
        order = Order.objects.create(**self.order_data)
        self.assertEqual(order.total, 150.50)
        self.assertEqual(order.order_status, "PENDING")
        self.assertEqual(order.delivery_type, "DELIVERY")

    def test_order_default_status(self):
        """Test order has default status PENDING"""
        order = Order.objects.create(**self.order_data)
        self.assertEqual(order.order_status, "PENDING")

    def test_order_status_choices(self):
        """Test all valid order statuses"""
        statuses = [
            "PENDING",
            "PAID",
            "PROCESSING",
            "IN_TRANSIT",
            "COMPLETED",
            "CANCELLED",
        ]
        for status_choice in statuses:
            data = self.order_data.copy()
            order = Order.objects.create(order_status=status_choice, **data)
            self.assertEqual(order.order_status, status_choice)

    def test_order_delivery_type_choices(self):
        """Test delivery type choices"""
        for delivery_type in ["PICKUP", "DELIVERY"]:
            data = self.order_data.copy()
            data["delivery_type"] = delivery_type
            order = Order.objects.create(**data)
            self.assertEqual(order.delivery_type, delivery_type)

    def test_order_string_representation(self):
        """Test order __str__ method"""
        order = Order.objects.create(**self.order_data)
        self.assertIn("Fresh Market", str(order))
        self.assertIn("Green Farm", str(order))
        self.assertIn("PENDING", str(order))


class OrderAPITests(APITestCase):
    """Test cases for Order API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.order_url = "/api/orders/"

        # Create farmer user and profile
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

        # Create buyer user and profile
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

        self.order_data = {
            "buyer": str(self.buyer_profile.id),
            "farmer": str(self.farmer_profile.id),
            "total": "150.50",
            "delivery_type": "DELIVERY",
        }

    def test_create_order_authenticated(self):
        """Test creating an order with authentication"""
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.post(self.order_url, self.order_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["order_status"], "PENDING")

    def test_create_order_unauthenticated(self):
        """Test creating order without authentication"""
        response = self.client.post(self.order_url, self.order_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_orders_buyer(self):
        """Test buyer can only see their own orders"""
        # Create order as buyer
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )

        # Create another buyer and their order
        other_buyer_user = User.objects.create_user(
            full_name="Other Buyer",
            email="other@example.com",
            phone_number="+1111111111",
            password="testpass123",
            role="BUYER",
        )
        other_buyer_profile = BuyerProfile.objects.create(
            user=other_buyer_user,
            business_name="Other Business",
            buyer_type="WHOLESALER",
            location="Other Location",
        )
        Order.objects.create(
            buyer=other_buyer_profile,
            farmer=self.farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
        )

        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_orders_farmer(self):
        """Test farmer can only see orders for their produce"""
        # Create order for this farmer
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )

        # Create another farmer and their order
        other_farmer_user = User.objects.create_user(
            full_name="Other Farmer",
            email="other_farmer@example.com",
            phone_number="+2222222222",
            password="testpass123",
            role="SELLER",
        )
        other_farmer_profile = FarmerProfile.objects.create(
            user=other_farmer_user,
            farm_name="Other Farm",
            farm_location="Other Location",
        )
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=other_farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
        )

        self.client.force_authenticate(user=self.farmer_user)
        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_order(self):
        """Test retrieving order details"""
        order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )
        self.client.force_authenticate(user=self.buyer_user)
        url = f"{self.order_url}{order.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], "100.00")

    def test_update_order_status(self):
        """Test updating order status"""
        order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )
        self.client.force_authenticate(user=self.farmer_user)
        url = f"{self.order_url}{order.id}/update_status/"
        response = self.client.patch(url, {"order_status": "PAID"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order_status"], "PAID")

    def test_my_orders_endpoint(self):
        """Test getting user's own orders"""
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.order_url}my_orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_pending_orders_endpoint(self):
        """Test getting pending orders"""
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
            order_status="PENDING",
        )
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
            order_status="PAID",
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.order_url}pending_orders/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_by_status_endpoint(self):
        """Test filtering orders by status"""
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
            order_status="PENDING",
        )
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
            order_status="COMPLETED",
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.order_url}by_status/?status=COMPLETED")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_order_status(self):
        """Test filtering orders via query parameter"""
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
            order_status="PENDING",
        )
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
            order_status="PAID",
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.order_url}?order_status=PAID")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_delivery_type(self):
        """Test filtering orders by delivery type"""
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )
        Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=200.00,
            delivery_type="PICKUP",
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.order_url}?delivery_type=PICKUP")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_order(self):
        """Test deleting an order"""
        order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=100.00,
            delivery_type="DELIVERY",
        )
        self.client.force_authenticate(user=self.buyer_user)
        url = f"{self.order_url}{order.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class OrderItemModelTests(TestCase):
    """Test cases for OrderItem model"""

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
            produce_name="Tomato",
            category="VEGETABLES",
            unit_price=2.50,
            quantity_available=100,
            harvest_date=date(2026, 5, 10),
        )

        # Create order
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=50.00,
            delivery_type="DELIVERY",
        )

    def test_create_order_item(self):
        """Test creating an order item"""
        item = OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.unit_price, 2.50)
        self.assertEqual(item.subtotal, 25.00)

    def test_order_item_subtotal_auto_calculation(self):
        """Test subtotal is automatically calculated"""
        item = OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=20,
            unit_price=3.00,
        )
        self.assertEqual(item.subtotal, 60.00)

    def test_order_item_string_representation(self):
        """Test order item __str__ method"""
        item = OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.assertIn("Tomato", str(item))
        self.assertIn("10", str(item))


class OrderItemAPITests(APITestCase):
    """Test cases for OrderItem API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.item_url = "/api/order-items/"

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
            produce_name="Tomato",
            category="VEGETABLES",
            unit_price=2.50,
            quantity_available=100,
            harvest_date=date(2026, 5, 10),
        )

        # Create order
        self.order = Order.objects.create(
            buyer=self.buyer_profile,
            farmer=self.farmer_profile,
            total=50.00,
            delivery_type="DELIVERY",
        )

        self.item_data = {
            "order": str(self.order.id),
            "produce": str(self.produce.id),
            "quantity": 10,
            "unit_price": "2.50",
        }

    def test_create_order_item(self):
        """Test creating an order item"""
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.post(self.item_url, self.item_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 10)
        self.assertEqual(float(response.data["subtotal"]), 25.00)

    def test_list_order_items(self):
        """Test listing order items"""
        OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(self.item_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_order_item(self):
        """Test retrieving an order item"""
        item = OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.client.force_authenticate(user=self.buyer_user)
        url = f"{self.item_url}{item.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 10)

    def test_update_order_item(self):
        """Test updating an order item"""
        item = OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.client.force_authenticate(user=self.buyer_user)
        url = f"{self.item_url}{item.id}/"
        response = self.client.patch(url, {"quantity": 20}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 20)
        self.assertEqual(float(response.data["subtotal"]), 50.00)

    def test_filter_by_order(self):
        """Test filtering items by order"""
        OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.item_url}?order={self.order.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_by_order_endpoint(self):
        """Test getting items by order via custom endpoint"""
        OrderItem.objects.create(
            order=self.order,
            produce=self.produce,
            quantity=10,
            unit_price=2.50,
        )
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(f"{self.item_url}by_order/?order_id={self.order.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
