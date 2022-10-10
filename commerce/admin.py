from django.contrib import admin

from commerce.models import Product, Order, Item, Address, OrderStatus, ProductImage, City, Category, ProductSize, Vendor, Merchant, \
    Label,ProductType

admin.site.register(Product)
#admin.site.register(Order)
admin.site.register(Item)
admin.site.register(Address)
admin.site.register(OrderStatus)
admin.site.register(ProductImage)
admin.site.register(City)
admin.site.register(Category)
admin.site.register(Vendor)
admin.site.register(Merchant)
admin.site.register(Label)
admin.site.register(ProductSize)
admin.site.register(ProductType)

from django.urls import reverse
from django.utils.html import format_html

@admin.register(Order)
class Orderadmin(admin.ModelAdmin):
    list_display = ("user","link_to_address","total","note","ordered","status")
    def link_to_address(self, obj):
        link = reverse("admin:commerce_address_change", args=[obj.address_id])
        return format_html('<a href="{}">{}</a>', link, obj.address)
    link_to_address.short_description = 'Address'
    list_filter = ("status__title","ordered")
    search_fields =["ordered","status__title"]

