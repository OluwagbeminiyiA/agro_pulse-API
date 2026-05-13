from datetime import timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from psycopg2.extras import Json

from core_agropulse.accounts.models import (
    BuyerProfile,
    FarmerProfile,
    TransporterProfile,
    User,
)
from core_agropulse.delivery.models import Delivery, RiderEarnings
from core_agropulse.orders.models import Order, OrderItem
from core_agropulse.payments.models import (
    EscrowAccount,
    Payment,
    PaymentSplit,
    Payout,
    VirtualAccount,
    VirtualAccountTransaction,
)
from core_agropulse.predictions.models import BuyerBehaviorPrediction, DemandForecast
from core_agropulse.produce.models import Produce
from core_agropulse.subscriptions.models import (
    Subscription,
    SubscriptionOrder,
    SubscriptionPayment,
)


class Command(BaseCommand):
    help = "Populate the database with Nigerian mock data."

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write(
                self.style.WARNING("Database already has data. Nothing was created.")
            )
            return

        rng = random.Random(20260513)
        today = timezone.now().date()

        farmer_specs = [
            {
                "full_name": "Amina Yusuf",
                "email": "amina.yusuf@agropulse.ng",
                "phone": "+2348012345601",
                "farm_name": "Kano Fresh Harvest",
                "farm_location": "Kaduna North, Kaduna",
                "trust_score": Decimal("4.80"),
            },
            {
                "full_name": "Chinedu Okafor",
                "email": "chinedu.okafor@agropulse.ng",
                "phone": "+2348012345602",
                "farm_name": "Anambra Green Fields",
                "farm_location": "Awka South, Anambra",
                "trust_score": Decimal("4.65"),
            },
            {
                "full_name": "Musa Bello",
                "email": "musa.bello@agropulse.ng",
                "phone": "+2348012345603",
                "farm_name": "Plateau Valley Farm",
                "farm_location": "Jos North, Plateau",
                "trust_score": Decimal("4.40"),
            },
        ]

        buyer_specs = [
            {
                "full_name": "Tunde Adeyemi",
                "email": "tunde.adeyemi@lagosfoods.ng",
                "phone": "+2348023456701",
                "business_name": "Lagos Street Kitchens",
                "buyer_type": "RESTAURANT",
                "location": "Ikeja, Lagos",
            },
            {
                "full_name": "Zainab Ibrahim",
                "email": "zainab.ibrahim@marketlink.ng",
                "phone": "+2348023456702",
                "business_name": "Sabon Gari Market Supplies",
                "buyer_type": "WHOLESALER",
                "location": "Sabon Gari, Kano",
            },
            {
                "full_name": "Efe Okoro",
                "email": "efe.okoro@freshcorner.ng",
                "phone": "+2348023456703",
                "business_name": "Fresh Corner Store",
                "buyer_type": "INDIVIDUAL",
                "location": "Gwarinpa, Abuja",
            },
        ]

        transporter_specs = [
            {
                "full_name": "Ibrahim Danladi",
                "email": "ibrahim.danladi@haul.ng",
                "phone": "+2348034567801",
                "vehicle_type": "Pickup Truck",
                "plate_number": "LAG-482KT",
                "service_area": "Lagos Mainland",
            },
            {
                "full_name": "Ngozi Eze",
                "email": "ngozi.eze@haul.ng",
                "phone": "+2348034567802",
                "vehicle_type": "Delivery Van",
                "plate_number": "ABJ-917QN",
                "service_area": "Abuja Central",
            },
        ]

        produce_specs = [
            (0, "Tomatoes", "VEGETABLES", Decimal("1800.00"), 160, 4),
            (0, "Ata Rodo Pepper", "VEGETABLES", Decimal("1500.00"), 120, 6),
            (0, "Mango", "FRUITS", Decimal("900.00"), 210, 10),
            (1, "White Yam", "OTHER", Decimal("3500.00"), 95, 8),
            (1, "Cassava Tubers", "OTHER", Decimal("2600.00"), 140, 12),
            (1, "Okra", "VEGETABLES", Decimal("1200.00"), 180, 3),
            (2, "Maize", "GRAINS", Decimal("2400.00"), 250, 15),
            (2, "Catfish", "MEAT", Decimal("4200.00"), 70, 5),
            (2, "Fresh Milk", "DAIRY", Decimal("1600.00"), 110, 2),
        ]

        def make_user(spec, role):
            return User.objects.create_user(
                email=spec["email"],
                password="Password123!",
                full_name=spec["full_name"],
                phone_number=spec["phone"],
                role=role,
            )

        with transaction.atomic():
            farmers = []
            buyers = []
            transporters = []

            for spec in farmer_specs:
                user = make_user(spec, "SELLER")
                farmers.append(
                    FarmerProfile.objects.create(
                        user=user,
                        farm_name=spec["farm_name"],
                        farm_location=spec["farm_location"],
                        trust_score=spec["trust_score"],
                    )
                )

            for spec in buyer_specs:
                user = make_user(spec, "BUYER")
                buyers.append(
                    BuyerProfile.objects.create(
                        user=user,
                        business_name=spec["business_name"],
                        buyer_type=spec["buyer_type"],
                        location=spec["location"],
                    )
                )

            for spec in transporter_specs:
                user = make_user(spec, "TRANSPORTER")
                transporters.append(
                    TransporterProfile.objects.create(
                        user=user,
                        vehicle_type=spec["vehicle_type"],
                        plate_number=spec["plate_number"],
                        service_area=spec["service_area"],
                    )
                )

            produce_lookup = {}
            for (
                farmer_index,
                name,
                category,
                unit_price,
                quantity,
                harvest_days_ago,
            ) in produce_specs:
                farmer = farmers[farmer_index]
                produce = Produce.objects.create(
                    farmer=farmer,
                    produce_name=name,
                    category=category,
                    unit_price=unit_price,
                    quantity_available=quantity,
                    harvest_date=today - timedelta(days=harvest_days_ago),
                    availability_status="AVAILABLE" if quantity > 100 else "LOW_STOCK",
                )
                produce_lookup[(farmer.id, name)] = produce

            order_specs = [
                {
                    "buyer": buyers[0],
                    "farmer": farmers[0],
                    "delivery_type": "DELIVERY",
                    "status": "COMPLETED",
                    "transporter": transporters[0],
                    "address": "12 Allen Avenue, Ikeja, Lagos",
                    "items": [("Tomatoes", 12), ("Ata Rodo Pepper", 10)],
                },
                {
                    "buyer": buyers[1],
                    "farmer": farmers[1],
                    "delivery_type": "DELIVERY",
                    "status": "IN_TRANSIT",
                    "transporter": transporters[1],
                    "address": "Sabon Gari Market, Kano",
                    "items": [("White Yam", 8), ("Cassava Tubers", 6)],
                },
                {
                    "buyer": buyers[2],
                    "farmer": farmers[2],
                    "delivery_type": "PICKUP",
                    "status": "PAID",
                    "transporter": None,
                    "address": "Wuse Market, Abuja",
                    "items": [("Maize", 15), ("Fresh Milk", 4)],
                },
                {
                    "buyer": buyers[0],
                    "farmer": farmers[1],
                    "delivery_type": "DELIVERY",
                    "status": "PROCESSING",
                    "transporter": transporters[0],
                    "address": "Surulere, Lagos",
                    "items": [("Okra", 14), ("Cassava Tubers", 5)],
                },
                {
                    "buyer": buyers[1],
                    "farmer": farmers[2],
                    "delivery_type": "DELIVERY",
                    "status": "PAID",
                    "transporter": transporters[1],
                    "address": "Bompai, Kano",
                    "items": [("Catfish", 6), ("Maize", 10)],
                },
            ]

            orders = []
            for index, spec in enumerate(order_specs):
                order = Order.objects.create(
                    buyer=spec["buyer"],
                    farmer=spec["farmer"],
                    total=Decimal("0.00"),
                    order_status=spec["status"],
                    delivery_type=spec["delivery_type"],
                )

                item_total = Decimal("0.00")
                for produce_name, quantity in spec["items"]:
                    produce = produce_lookup[(spec["farmer"].id, produce_name)]
                    item = OrderItem.objects.create(
                        order=order,
                        produce=produce,
                        quantity=quantity,
                        unit_price=produce.unit_price,
                        subtotal=Decimal("0.00"),
                    )
                    item_total += item.subtotal

                order.total = item_total
                order.save(update_fields=["total", "updated_at"])
                orders.append((order, spec))

            for index, (order, spec) in enumerate(orders):
                payment = Payment.objects.create(
                    buyer=spec["buyer"],
                    order=order,
                    email=spec["buyer"].user.email,
                    squad_transaction_id=f"SQD-NG-{index + 1:04d}",
                    payment_method="card",
                    payment_status="SUCCESS"
                    if order.order_status != "PENDING"
                    else "PENDING",
                    amount=order.total,
                    currency="NGN",
                    channel="CARD",
                    gateway_response='{"status":"success","message":"Mock payment"}',
                    metadata={"source": "seed", "country": "NG"},
                    checkout_url=f"https://pay.agropulse.ng/checkout/{index + 1}",
                    webhook_recieved=True,
                    webhook_verified=True,
                    webhook_payload={"event": "payment.success", "seed": True},
                    escrow_enabled=True,
                )

                delivery = Delivery.objects.create(
                    order=order,
                    transporter=spec["transporter"],
                    delivery_status="DELIVERED"
                    if order.order_status == "COMPLETED"
                    else "IN_TRANSIT"
                    if order.order_status == "IN_TRANSIT"
                    else "PENDING",
                    delivery_address=spec["address"],
                    picked_up_at=timezone.now() - timedelta(days=1)
                    if spec["transporter"]
                    else None,
                    delivered_at=timezone.now()
                    if order.order_status == "COMPLETED"
                    else None,
                )

                if spec["transporter"] is not None:
                    rider_amount = (order.total * Decimal("0.10")).quantize(
                        Decimal("0.01")
                    )
                    platform_fee = Decimal("500.00")
                    farmer_amount = (
                        order.total - rider_amount - platform_fee
                    ).quantize(Decimal("0.01"))
                else:
                    rider_amount = Decimal("0.00")
                    platform_fee = Decimal("250.00")
                    farmer_amount = (order.total - platform_fee).quantize(
                        Decimal("0.01")
                    )

                PaymentSplit.objects.create(
                    payment=payment,
                    farmer_amount=farmer_amount,
                    rider_amount=rider_amount,
                    platform_fee=platform_fee,
                    farmer_processed=payment.payment_status == "SUCCESS",
                    rider_processed=payment.payment_status == "SUCCESS"
                    and spec["transporter"] is not None,
                )

                if payment.payment_status == "SUCCESS":
                    EscrowAccount.objects.create(
                        payment=payment,
                        farmer=spec["farmer"],
                        amount_held=order.total,
                        release_status="RELEASED"
                        if order.order_status == "COMPLETED"
                        else "HELD",
                        released_at=timezone.now()
                        if order.order_status == "COMPLETED"
                        else None,
                    )
                    Payout.objects.create(
                        payment=payment,
                        farmer=spec["farmer"],
                        payout_type="FARMER",
                        amount=farmer_amount,
                        payout_status="COMPLETED"
                        if order.order_status == "COMPLETED"
                        else "PROCESSING",
                        bank_reference=f"NG-PAYOUT-F-{index + 1:04d}",
                        completed_at=timezone.now()
                        if order.order_status == "COMPLETED"
                        else None,
                    )
                    if spec["transporter"] is not None:
                        Payout.objects.create(
                            payment=payment,
                            rider=spec["transporter"],
                            payout_type="RIDER",
                            amount=rider_amount,
                            payout_status="COMPLETED"
                            if order.order_status == "COMPLETED"
                            else "PROCESSING",
                            bank_reference=f"NG-PAYOUT-R-{index + 1:04d}",
                            completed_at=timezone.now()
                            if order.order_status == "COMPLETED"
                            else None,
                        )

                        RiderEarnings.objects.create(
                            transporter=spec["transporter"],
                            delivery=delivery,
                            earnings_amount=rider_amount,
                            payment_status="PAID"
                            if order.order_status == "COMPLETED"
                            else "PENDING",
                            paid_at=timezone.now()
                            if order.order_status == "COMPLETED"
                            else None,
                        )

            for farmer in farmers:
                VirtualAccount.objects.create(
                    farmer=farmer,
                    transporter=None,
                    virtual_account_number=f"10{rng.randint(100000000, 999999999)}",
                    bank_name=rng.choice(["Access Bank", "Zenith Bank", "GTBank"]),
                    account_name=farmer.user.full_name,
                    first_name=farmer.user.full_name.split()[0],
                    last_name=farmer.user.full_name.split()[-1],
                    email=farmer.user.email,
                    mobile_num=farmer.user.phone_number,
                    bvn=f"{rng.randint(10000000000, 99999999999)}",
                )

            for transporter in transporters:
                VirtualAccount.objects.create(
                    farmer=None,
                    transporter=transporter,
                    virtual_account_number=f"20{rng.randint(100000000, 999999999)}",
                    bank_name=rng.choice(["First Bank", "UBA", "Polaris Bank"]),
                    account_name=transporter.user.full_name,
                    first_name=transporter.user.full_name.split()[0],
                    last_name=transporter.user.full_name.split()[-1],
                    email=transporter.user.email,
                    mobile_num=transporter.user.phone_number,
                    bvn=f"{rng.randint(10000000000, 99999999999)}",
                )

            for account in VirtualAccount.objects.all():
                for offset in range(2):
                    principal_amount = Decimal(
                        rng.choice(["15000.00", "24000.00", "38000.00"])
                    )
                    fee = Decimal("250.00")
                    VirtualAccountTransaction.objects.create(
                        virtual_account=account,
                        transaction_reference=f"NG-VA-{account.virtual_account_number}-{offset + 1}",
                        pricipal_amount=principal_amount,
                        settled_amount=principal_amount - fee,
                        fee=fee,
                        sender=rng.choice(
                            ["Market Basket Nigeria", "Canteen Connect", "Harvest Hub"]
                        ),
                        remarks="Mock settlement for local produce sales",
                        currency="NGN",
                        transaction_date=timezone.now() - timedelta(days=offset),
                        webhook_processed=True,
                        webhook_payload={"seed": True, "settled": True},
                    )

            subscription_specs = [
                (
                    buyers[0],
                    farmers[0],
                    produce_lookup[(farmers[0].id, "Tomatoes")],
                    "WEEKLY",
                    12,
                ),
                (
                    buyers[1],
                    farmers[1],
                    produce_lookup[(farmers[1].id, "White Yam")],
                    "MONTHLY",
                    20,
                ),
                (
                    buyers[2],
                    farmers[2],
                    produce_lookup[(farmers[2].id, "Maize")],
                    "DAILY",
                    8,
                ),
            ]

            subscriptions = []
            for index, (buyer, farmer, produce, frequency, quantity) in enumerate(
                subscription_specs
            ):
                subscription = Subscription.objects.create(
                    buyer=buyer,
                    farmer=farmer,
                    produce=produce,
                    frequency=frequency,
                    expected_quantity=quantity,
                    next_expected_order_date=today + timedelta(days=7 * (index + 1)),
                    active=True,
                    status="ACTIVE",
                )
                subscriptions.append(subscription)

                subscription_order = SubscriptionOrder.objects.create(
                    subscription=subscription,
                    quantity=quantity,
                    unit_price=produce.unit_price,
                    total_amount=(produce.unit_price * quantity).quantize(
                        Decimal("0.01")
                    ),
                    order_status="CONFIRMED",
                    scheduled_date=today + timedelta(days=7 * (index + 1)),
                )
                SubscriptionPayment.objects.create(
                    subscription_order=subscription_order,
                    amount=subscription_order.total_amount,
                    payment_status="COMPLETED",
                    payment_method="auto-debit",
                    payment_date=timezone.now(),
                )

            demand_targets = [
                produce_lookup[(farmers[0].id, "Tomatoes")],
                produce_lookup[(farmers[1].id, "Cassava Tubers")],
                produce_lookup[(farmers[2].id, "Maize")],
            ]
            for index, produce in enumerate(demand_targets):
                DemandForecast.objects.create(
                    produce=produce,
                    predicted_demand_volume=produce.quantity_available
                    + rng.randint(40, 120),
                    forecast_period=rng.choice(["weekly", "biweekly", "monthly"]),
                    demand_spike_probability=Decimal(
                        str(rng.choice(["55.00", "68.00", "82.00"]))
                    ),
                    recommended_stock_level=produce.quantity_available
                    + rng.randint(30, 90),
                )

            for buyer, produce in [
                (buyers[0], produce_lookup[(farmers[0].id, "Tomatoes")]),
                (buyers[1], produce_lookup[(farmers[1].id, "Cassava Tubers")]),
                (buyers[2], produce_lookup[(farmers[2].id, "Maize")]),
            ]:
                BuyerBehaviorPrediction.objects.create(
                    buyer_id=buyer,
                    produce_id=produce,
                    predicted_return_date=today + timedelta(days=rng.randint(5, 21)),
                    predicted_quantity=rng.randint(5, 25),
                    return_probability=Decimal(
                        str(rng.choice(["61.00", "73.00", "88.00"]))
                    ),
                    buyer_category=buyer.buyer_type,
                )

            self._seed_transfer_rows(farmers, transporters)

        self.stdout.write(
            self.style.SUCCESS("Nigerian mock data created successfully.")
        )

    def _seed_transfer_rows(self, farmers, transporters):
        table_names = set(connection.introspection.table_names())
        if "payments_transfer" not in table_names:
            return

        now = timezone.now()
        rows = [
            (
                "NG-TRF-0001",
                Decimal("12500.00"),
                "100001",
                "0123456789",
                farmers[0].user.full_name,
                "Mock farmer settlement",
                "success",
                Json({"seed": True}),
                None,
                now,
                now,
                farmers[0].id,
                transporters[0].id,
            ),
            (
                "NG-TRF-0002",
                Decimal("9800.00"),
                "100002",
                "0987654321",
                transporters[1].user.full_name,
                "Mock rider settlement",
                "pending",
                Json({"seed": True}),
                None,
                now,
                now,
                farmers[1].id,
                transporters[1].id,
            ),
        ]

        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO payments_transfer (
                    transaction_reference,
                    amount,
                    bank_code,
                    account_number,
                    account_name,
                    remark,
                    status,
                    squad_response,
                    error_message,
                    created_at,
                    updated_at,
                    farmer_id,
                    transporter_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                rows,
            )
