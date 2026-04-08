from django.contrib import admin
from .models import Item, Order, OrderItem, Address, Payment

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["user", "ordered"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    def quantity_orderitem(self):
        return str(self)
    
    list_display = [quantity_orderitem, "ordered"]
    
    quantity_orderitem.short_description = "Quantity/OrderItem"


admin.site.register(Item)
admin.site.register(Address)
admin.site.register(Payment)
# Register your models here.
