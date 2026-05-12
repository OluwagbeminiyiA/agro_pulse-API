import requests
import hashlib
import hmac
import json

from cfgv import ValidationError
from django.conf import settings


class SquadAPIError(Exception):
    pass


class SquadService:
    def __init__(self):
        self.secret_key = settings.SQUAD_SECRET_KEY
        self.public_key = settings.SQUAD_PUBLIC_KEY
        self.merchant_id = settings.SQUAD_MERCHANT_ID
        self.base_url = "https://sandbox-api-d.squadco.com"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method, endpoint, data=None, params=None):
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=30
                )
            if method == "POST":
                response = requests.post(
                    url, headers=self.headers, json=data, timeout=30
                )
            if method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValidationError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise SquadAPIError(f"API request failed: {str(e)}")

    def initiate_payment(
        self,
        email,
        amount,
        currency,
        transaction_ref=None,
        callback_url=None,
        metadata=None,
        payment_channels=None,
        pass_charge=False,
    ):

        endpoint = "/transaction/initiate"

        data = {
            "email": email,
            "amount": amount,
            "currency": currency,
            "initiate_type": "inline",
            "pass_charge": pass_charge,
        }

        if transaction_ref:
            data["transaction_ref"] = transaction_ref

        if callback_url:
            data["callback_url"] = callback_url

        if metadata:
            data["metadata"] = metadata

        if payment_channels:
            data["payment_channels"] = payment_channels

        response = self._make_request("POST", endpoint, data)

        if not response.get("SUCCESS"):
            raise SquadAPIError(f"Payment Initiation failed: {response.get('message')}")
        return response["data"]

    def verify_payment(self, transaction_ref):
        endpoint = f"/transaction/verify/{transaction_ref}"
        response = self._make_request("GET", endpoint)

        if not response.get("success"):
            raise SquadAPIError(
                f"Payment Verification failed: {response.get('message')}"
            )

        return response["data"]

    def create_virtual_account(
        self,
        customer,
        first_name,
        last_name,
        mobile_num,
        email,
        bvn,
        dob,
        address=None,
        gender=None,
        beneficiary_account=None,
    ):

        endpoint = "/virtual-account"
        data = {
            "customer_identifier": customer,
            "first_name": first_name,
            "last_name": last_name,
            "mobile_num": mobile_num,
            "email": email,
            "bvn": bvn,
            "dob": dob,
        }

        if address:
            data["address"] = address

        if gender:
            data["gender"] = gender

        if beneficiary_account:
            data["beneficiary_account"] = beneficiary_account

        response = self._make_request("POST", endpoint, data=data)

        if not response.get("SUCCESS"):
            raise SquadAPIError(
                f"Virtual account creation failed: {response.get('message')}"
            )

        return response["data"]

    def get_virtual_account_transactions(self, customer_identifier):

        endpoint = f"/virtual-account/customer/transactions/{customer_identifier}"
        response = self._make_request("GET", endpoint)

        if not response.get("success"):
            raise SquadAPIError(
                f"Failed to get transactions: {response.get('message')}"
            )

        return response["data"]

    def get_missed_webhooks(self):

        endpoint = "/virtual-account/webhook/logs"
        response = self._make_request("GET", endpoint)

        if not response.get("success"):
            raise SquadAPIError(
                f"Failed to get missed webhooks: {response.get('message')}"
            )

        return response["data"]

    def delete_webhook_log(self, transaction_reference):

        endpoint = f"/virtual-account/webhook/logs/{transaction_reference}"
        response = self._make_request("DELETE", endpoint)

        if not response.get("success"):
            raise SquadAPIError(
                f"Failed to delete webhook log: {response.get('message')}"
            )

        return response

    def lookup_account(self, bank_code, account_number):

        endpoint = "/payout/account/lookup"
        params = {"bank_code": bank_code, "account_number": account_number}

        response = self._make_request("GET", endpoint, params=params)

        if not response.get("success"):
            raise SquadAPIError(f"Account lookup failed: {response.get('message')}")

        return response["data"]

    def initiate_transfer(
        self,
        transaction_reference,
        amount,
        bank_code,
        account_number,
        account_name,
        remark=None,
    ):

        # Ensure transaction reference is prefixed with merchant ID
        if not transaction_reference.startswith(f"{self.merchant_id}_"):
            transaction_reference = f"{self.merchant_id}_{transaction_reference}"

        endpoint = "/payout/transfer"

        data = {
            "transaction_reference": transaction_reference,
            "amount": amount,
            "bank_code": bank_code,
            "account_number": account_number,
            "account_name": account_name,
            "currency_id": "NGN",
        }

        if remark:
            data["remark"] = remark

        response = self._make_request("POST", endpoint, data=data)

        if not response.get("success"):
            raise SquadAPIError(
                f"Transfer initiation failed: {response.get('message')}"
            )

        return response["data"]

    def requery_transfer(self, transaction_reference):

        endpoint = "/payout/requery"
        data = {"transaction_reference": transaction_reference}

        response = self._make_request("POST", endpoint, data=data)

        if not response.get("success"):
            raise SquadAPIError(f"Transfer requery failed: {response.get('message')}")

        return response["data"]

    def verify_webhook_signature(self, payload, signature):

        payload_string = json.dumps(payload, separators=(",", ":"))

        # Create HMAC SHA-512 hash
        computed_signature = (
            hmac.new(
                key=self.secret_key.encode("utf-8"),
                msg=payload_string.encode("utf-8"),
                digestmod=hashlib.sha512,
            )
            .hexdigest()
            .upper()
        )

        # Compare signatures
        return hmac.compare_digest(computed_signature, signature.upper())


class PaymentService:
    """Service for handling payment business logic"""

    @staticmethod
    def create_escrow(payment):
        """Create escrow account for payment"""
        from core_agropulse.payments.models import EscrowAccount

        if hasattr(payment, "escrow"):
            return

        EscrowAccount.objects.create(
            payment=payment,
            farmer=payment.order.farmer,
            amount_held=payment.amount,
        )

    @staticmethod
    def create_payment_split(payment):
        """Create payment split for farmer, rider, and platform"""
        from decimal import Decimal

        from core_agropulse.payments.models import PaymentSplit

        if hasattr(payment, "split"):
            return

        # Calculate split: 80% farmer, 10% rider, 10% platform
        farmer_amount = payment.amount * Decimal("0.80")
        rider_amount = payment.amount * Decimal("0.10")
        platform_fee = payment.amount * Decimal("0.10")

        PaymentSplit.objects.create(
            payment=payment,
            farmer_amount=farmer_amount,
            rider_amount=rider_amount,
            platform_fee=platform_fee,
        )
