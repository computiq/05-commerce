import random
import string
from typing import List

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Product, Category, City, Vendor, Item, Order, OrderStatus, Address
from commerce.schemas import ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemSchema, ItemCreate, AddressOut, AddressCreate, AddressSchema, AddressUpdate, CheckOut
from config.utils.schemas import MessageOut

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])

User = get_user_model()

@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    return Vendor.objects.all()


@products_controller.get('', response={
    200: List[ProductOut],
    404: MessageOut
})
def list_products(
        request, *,
        q: str = None,
        price_from: int = None,
        price_to: int = None,
        vendor=None,
):
    products_qs = Product.objects.filter(is_active=True).select_related('merchant', 'vendor', 'category', 'label')

    if not products_qs:
        return 404, {'detail': 'No products found'}

    if q:
        products_qs = products_qs.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        )

    if price_from:
        products_qs = products_qs.filter(discounted_price__gte=price_from)

    if price_to:
        products_qs = products_qs.filter(discounted_price__lte=price_to)

    if vendor:
        products_qs = products_qs.filter(vendor_id=vendor)

    return products_qs


"""
# product = Product.objects.all().select_related('merchant', 'category', 'vendor', 'label')
    # print(product)
    #
    # order = Product.objects.all().select_related('address', 'user').prefetch_related('items')

    # try:
    #     one_product = Product.objects.get(id='8d3dd0f1-2910-457c-89e3-1b0ed6aa720a')
    # except Product.DoesNotExist:
    #     return {"detail": "Not found"}
    # print(one_product)
    #
    # shortcut_function = get_object_or_404(Product, id='8d3dd0f1-2910-457c-89e3-1b0ed6aa720a')
    # print(shortcut_function)

    # print(type(product))
    # print(product.merchant.name)
    # print(type(product.merchant))
    # print(type(product.category))


Product <- Merchant, Label, Category, Vendor

Retrieve 1000 Products form DB

products = Product.objects.all()[:1000] (select * from product limit 1000)

for p in products:
    print(p)
    
for every product, we retrieve (Merchant, Label, Category, Vendor) records

Merchant.objects.get(id=p.merchant_id) (select * from merchant where id = 'p.merchant_id')
Label.objects.get(id=p.label_id) (select * from merchant where id = 'p.label_id')
Category.objects.get(id=p.category_id) (select * from merchant where id = 'p.category_id')
Vendor.objects.get(id=p.vendor_id) (select * from merchant where id = 'p.vendor_id')

4*1000+1

Solution: Eager loading

products = (select * from product limit 1000)

mids = [p1.merchant_id, p2.merchant_id, ...]
[p1.label_id, p2.label_id, ...]
.
.
.

select * from merchant where id in (mids) * 4 for (label, category and vendor)

4+1

"""


@address_controller.get('addresses', response={
    200: List[AddressOut],
    400: MessageOut
})
def list_addresses(request):
    addresses_qs = Address.objects.all()
    if addresses_qs:
        return addresses_qs
    else:
        return 400, {'detail': 'No addresses found'}


@address_controller.post("add-address", auth=GlobalAuth() ,response=MessageOut)
def create_address(request, data_in: AddressCreate):
    user = get_object_or_404(User, id=request.auth["pk"])
    address = Address(**data_in.dict())
    address.user = user
    address.save()
    return {'detail': 'Address added succsesfully'}


@address_controller.post("update-address", auth=GlobalAuth(), response=MessageOut)
def update_address(request, data_in: AddressUpdate):
    address = get_object_or_404(Address, id=data_in.id)

    for attr, value in data_in.dict().items():
        setattr(address, attr, value)
    address.save()

    return {'detail': 'Address updated succsesfully'}


# @products_controller.get('categories', response=List[CategoryOut])
# def list_categories(request):
#     return Category.objects.all()


@address_controller.get('cities', response={
    200: List[CitiesOut],
    404: MessageOut
})
def list_cities(request):
    cities_qs = City.objects.all()

    if cities_qs:
        return cities_qs

    return 404, {'detail': 'No cities found'}


@address_controller.get('cities/{id}', response={
    200: CitiesOut,
    404: MessageOut
})
def retrieve_city(request, id: UUID4):
    return get_object_or_404(City, id=id)


@address_controller.post('cities', auth=GlobalAuth(), response={
    201: CitiesOut,
    400: MessageOut
})
def create_city(request, city_in: CitySchema):
    city = City(**city_in.dict())
    city.save()
    return 201, city


@address_controller.put('cities/{id}', auth=GlobalAuth(), response={
    200: CitiesOut,
    400: MessageOut
})
def update_city(request, id: UUID4, city_in: CitySchema):
    city = get_object_or_404(City, id=id)
    city.name = city_in.name
    city.save()
    return 200, city


@address_controller.delete('cities/{id}',  auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_city(request, id: UUID4):
    city = get_object_or_404(City, id=id)
    city.delete()
    return 204, {'detail': ''}


@order_controller.get('cart', auth=GlobalAuth(), response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    user = get_object_or_404(User, id=request.auth["pk"])
    cart_items = Item.objects.filter(user=user, ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    user = get_object_or_404(User, id=request.auth["pk"])
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=user)
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=user)

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth["pk"])
    item = get_object_or_404(Item, id=id, user=User.objects.first())
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.delete('item/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    user = get_object_or_404(User, id=request.auth["pk"])
    item = get_object_or_404(Item, id=id, user=User.objects.first())
    item.delete()

    return 204, {'detail': 'Item deleted!'}


def generate_ref_code():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


@order_controller.post("create", auth=GlobalAuth(), response={
    200: MessageOut
})
def create_order(request):
    user = get_object_or_404(User, id=request.auth["pk"])
    items = Item.objects.filter(user=User.objects.first()).filter(ordered=false)

    items.update(ordered=True)

    order = Order(
        user=User.objects.first(),
        ref_code=ref_code(),
        status=OrderStatus.objects.get(is_default=True),
        ordered=False,
    )
    order.save()

    dic = list(items.values('id'))
    for entry in dic:
        print(entry["id"])
        order.items.add(entry["id"])
    order.total = order.order_total
    order.save()

    # debugging
    # print(order.items)

    return 200, {'detail': 'the order has been succsesfuly created'}


@order_controller.put('checkout', auth=GlobalAuth())
def checkout(request, data_in: CheckOut):
    user = get_object_or_404(User, id=request.auth["pk"])
    order = get_object_or_404(Order, user=user)
    order.note = data_in.note
    order.address = Address.objects.get(id=data_in.address_id)
    order.ordered = True
    order.status = OrderStatus.objects.get(title='PROCESSING')
    order.save()
    return 200, {'detail': 'Check out done sucsessfuly'}

def ref_code():
    x = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return x