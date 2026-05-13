from django.contrib import admin

from core_agropulse.predictions.models import BuyerBehaviorPrediction, DemandForecast

admin.site.register(BuyerBehaviorPrediction)
admin.site.register(DemandForecast)
