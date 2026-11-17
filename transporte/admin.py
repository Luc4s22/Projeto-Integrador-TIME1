from django.contrib import admin

from .models import Shipment, ShipmentItem


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'origin', 'destination', 'device', 'created_by', 'buyer', 'driver', 'status', 'started_at']
    list_select_related = ['origin', 'destination', 'device', 'created_by', 'buyer', 'driver']
    list_filter = ['status']
    inlines = [ShipmentItemInline]
