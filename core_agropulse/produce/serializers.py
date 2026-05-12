from rest_framework import serializers
from core_agropulse.produce.models import Produce


class ProduceSerializer(serializers.ModelSerializer):
    farmer_farm_name = serializers.CharField(source="farmer.farm_name", read_only=True)
    farmer_user_full_name = serializers.CharField(
        source="farmer.user.full_name", read_only=True
    )

    class Meta:
        model = Produce
        fields = [
            "id",
            "farmer",
            "farmer_farm_name",
            "farmer_user_full_name",
            "produce_name",
            "category",
            "unit_price",
            "quantity_available",
            "harvest_date",
            "availability_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProduceDetailSerializer(serializers.ModelSerializer):
    farmer_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Produce
        fields = [
            "id",
            "farmer",
            "farmer_details",
            "produce_name",
            "category",
            "unit_price",
            "quantity_available",
            "harvest_date",
            "availability_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_farmer_details(self, obj):
        return {
            "farm_name": obj.farmer.farm_name,
            "farm_location": obj.farmer.farm_location,
            "farmer_name": obj.farmer.user.full_name,
            "farmer_email": obj.farmer.user.email,
            "farmer_phone": obj.farmer.user.phone_number,
        }
