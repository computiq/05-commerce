from django.contrib import admin

from commerce.models import Product, Order, Item, Address, OrderStatus, ProductImage, City, Category, ProductSize, Vendor, Merchant, \
    Label,ProductType

admin.site.register(Product)
admin.site.register(Order)
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

