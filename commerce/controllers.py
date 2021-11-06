from typing import List
import string, random
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model, authenticate
from account.authorization import GlobalAuth
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4
from commerce.models import Address, Order, OrderStatus, Product, Category, City, Vendor, Item
from commerce.schemas import AddressOut, CheckOut, MessageOut, ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemSchema, ItemCreate, AddressPut

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])
checkout_controller = Router(tags=['checkout'])


@vendor_controller.get('', response=List[VendorOut])
def list_vendors(request):
    return Vendor.objects.all()


@products_controller.get('', auth=GlobalAuth(), response={
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


@address_controller.get('address', auth=GlobalAuth(), response={
    200: List[AddressOut],
    404: MessageOut
})
def list_addresses(request):
    addresses_qs = Address.objects.all()

    if addresses_qs:
        return addresses_qs

    return 404, {'detail': 'No addresses found'}



@address_controller.get('addresses/{id}', auth=GlobalAuth(), response={
    200: AddressOut,
    404: MessageOut
})
def retrieve_address(request, id: UUID4):
    return get_object_or_404(Address, id=id)


@address_controller.post('addresses', auth=GlobalAuth(), response={
    201: AddressOut,
    400: MessageOut
})
def create_address(request, address_in: AddressPut):
    # address = Address
    # address = address_in
    # address.city = City.objects.create(name=address_in.city)
    # address.address1 = address_in.address1
    # address.address2 = address_in.address2
    # address.phone = address_in.phone
    # address.work_address = address_in.work_address
    
    adress = Address(**address_in.dict(), user=request.auth['pk'])
    adress.save()
    return 200, adress

    # address.save()
    return 201


@address_controller.put('addresses/{id}', auth=GlobalAuth(), response={
    200: AddressOut,
    400: MessageOut
})
def update_address(request, id: UUID4, address_in: AddressPut):
    address = get_object_or_404(Address, id=id, user= User.objects.first())
    address.city.name = City.objects.update(name=address_in.city)
    address.address1 = address_in.address1
    address.address2 = address_in.address2
    address.phone = address_in.phone
    address.work_address = address_in.work_address
    address.save()
    return 200, address


@address_controller.delete('addresses/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_address(request, id: UUID4):
    city = get_object_or_404(Address, id=id)
    city.delete()
    return 204, {'detail': ''}












# @products_controller.get('categories', response=List[CategoryOut])
# def list_categories(request):
#     return Category.objects.all()


@address_controller.get('cities', auth=GlobalAuth(), response={
    200: List[CitiesOut],
    404: MessageOut
})
def list_cities(request):
    cities_qs = City.objects.all()

    if cities_qs:
        return cities_qs

    return 404, {'detail': 'No cities found'}


@address_controller.get('cities/{id}', auth=GlobalAuth(), response={
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


@address_controller.delete('cities/{id}', auth=GlobalAuth(), response={
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
    cart_items = Item.objects.filter(user=request.auth['pk'], ordered=False)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(), response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate):
    try:
        item = Item.objects.get(product_id=item_in.product_id, user=request.auth['pk'])
        item.item_qty += 1
        item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=User.objects.first())

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}



@order_controller.post('item/{id}/increase-quantity', auth=GlobalAuth(), response={
    200: MessageOut,
})
def increase_item_quantity(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.item_qty += 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}



@order_controller.delete('item/{id}', auth=GlobalAuth(), response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    item = get_object_or_404(Item, id=id, user=request.auth['pk'])
    item.delete()

    return 204, {'detail': 'Item deleted!'}


def refCode():
    return ''.join(random.sample(string.ascii_letters+string.digits,6))

@order_controller.post('create-order', auth=GlobalAuth(),)
def create_order(request):
    order = Order(
        user=request.auth['pk'],
        status=OrderStatus.objects.get(is_active=True),
        ref_code=refCode(),
        ordered = False 
    )
    user_items = Item.objects.filter(user=request.auth['pk'])
    user_items.update(ordered = True)
    order.items.append(*user_items)
    order = order.order_total
    order.save()
    return {'detail': 'order created successfully'}


@checkout_controller.post('checkout', auth=GlobalAuth(),)
def checkout(request, checkout_input: CheckOut):
    order_chckt = get_object_or_404(Order, user=request.auth['pk'], ordered=False)

    if order_chckt:
        order_chckt.address = Address.objects.get(id=checkout_input.address)
        order_chckt.note = checkout_input.note
        order_chckt.status = OrderStatus.objects.get(is_default=False)
        order_chckt.ordered = True
        order_chckt.save()
        return 200, {'detail': 'checkout done successfully'}

    return 404, {'detail': 'you have no active orders'}
