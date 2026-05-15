from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from core_agropulse.accounts.models import BuyerProfile, FarmerProfile
from core_agropulse.orders.models import Order, OrderItem
from core_agropulse.produce.models import Produce

User = get_user_model()


class PredictionRecommendationAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()

        self.buyer_user = User.objects.create_user(
            full_name="Buyer One",
            email="buyer.predictions@example.com",
            phone_number="+2348000000001",
            password="testpass123",
            role="BUYER",
        )
        self.buyer = BuyerProfile.objects.create(
            user=self.buyer_user,
            business_name="Urban Foods",
            buyer_type="RESTAURANT",
            location="Lagos",
        )

        self.farmer_user_1 = User.objects.create_user(
            full_name="Farmer One",
            email="farmer.one@example.com",
            phone_number="+2348000000002",
            password="testpass123",
            role="SELLER",
        )
        self.farmer_1 = FarmerProfile.objects.create(
            user=self.farmer_user_1,
            farm_name="Green Valley",
            farm_location="Lagos Mainland",
            trust_score=4.50,
        )

        self.farmer_user_2 = User.objects.create_user(
            full_name="Farmer Two",
            email="farmer.two@example.com",
            phone_number="+2348000000003",
            password="testpass123",
            role="SELLER",
        )
        self.farmer_2 = FarmerProfile.objects.create(
            user=self.farmer_user_2,
            farm_name="Prime Harvest",
            farm_location="Ibadan",
            trust_score=3.90,
        )

        self.produce = Produce.objects.create(
            farmer=self.farmer_1,
            produce_name="Tomato",
            category="VEGETABLES",
            unit_price="2500.00",
            quantity_available=250,
            harvest_date=timezone.now().date(),
            availability_status="AVAILABLE",
        )
        self.alt_produce = Produce.objects.create(
            farmer=self.farmer_2,
            produce_name="Tomato",
            category="VEGETABLES",
            unit_price="2300.00",
            quantity_available=180,
            harvest_date=timezone.now().date(),
            availability_status="AVAILABLE",
        )

        self._create_order_history()

    def _create_order_history(self):
        order_1 = Order.objects.create(
            buyer=self.buyer,
            farmer=self.farmer_1,
            total="10000.00",
            order_status="COMPLETED",
            delivery_type="DELIVERY",
        )
        OrderItem.objects.create(
            order=order_1,
            produce=self.produce,
            quantity=20,
            unit_price=Decimal("2500.00"),
        )

        order_2 = Order.objects.create(
            buyer=self.buyer,
            farmer=self.farmer_1,
            total="12000.00",
            order_status="COMPLETED",
            delivery_type="DELIVERY",
        )
        OrderItem.objects.create(
            order=order_2,
            produce=self.produce,
            quantity=24,
            unit_price=Decimal("2500.00"),
        )

        # Adjust timestamps to create realistic intervals for return prediction.
        now = timezone.now()
        Order.objects.filter(id=order_1.id).update(created_at=now - timedelta(days=16))
        Order.objects.filter(id=order_2.id).update(created_at=now - timedelta(days=6))

    def test_demand_recommendation_endpoint(self):
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(
            "/api/predictions/recommendations/demand/",
            {"produce_id": str(self.produce.id), "forecast_period": "weekly"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("demand_forecast", response.data)
        self.assertIn("predicted_demand_volume", response.data["demand_forecast"])

    def test_supplier_recommendation_endpoint(self):
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(
            "/api/predictions/recommendations/suppliers/",
            {
                "buyer_id": str(self.buyer.id),
                "produce_id": str(self.produce.id),
                "quantity_required": 50,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommendations", response.data)
        self.assertGreaterEqual(len(response.data["recommendations"]), 1)

    def test_buyer_return_recommendation_endpoint(self):
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(
            "/api/predictions/recommendations/buyer-return/",
            {
                "buyer_id": str(self.buyer.id),
                "produce_id": str(self.produce.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("buyer_return_prediction", response.data)
        self.assertIn("return_probability", response.data["buyer_return_prediction"])

    def test_summary_recommendation_endpoint(self):
        self.client.force_authenticate(user=self.buyer_user)
        response = self.client.get(
            "/api/predictions/recommendations/summary/",
            {
                "buyer_id": str(self.buyer.id),
                "produce_id": str(self.produce.id),
                "forecast_period": "biweekly",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("demand_forecast", response.data)
        self.assertIn("buyer_return_prediction", response.data)
        self.assertIn("supplier_recommendations", response.data)
