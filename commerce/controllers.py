import random
import string
from typing import List
from django.contrib import auth

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from ninja import Router
from pydantic import UUID4

from account.authorization import GlobalAuth
from commerce.models import Address, Product, Category, City, ProductSize, Vendor, Item, Order, OrderStatus,ProductType
from commerce.schemas import AddressIn,AddressOut,ProductTypeOut, ProductOut, CitiesOut, CitySchema, VendorOut, ItemOut, ItemSchema, ItemCreate,CategoryOut
from config.utils.schemas import MessageOut
import string
import random

products_controller = Router(tags=['products'])
address_controller = Router(tags=['addresses'])
vendor_controller = Router(tags=['vendors'])
order_controller = Router(tags=['orders'])
checkout_controller = Router(tags=['checkout'])
category_controllers = Router(tags=['Category'])


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
):
    products_qs = Product.objects.filter(is_active=True).select_related('category', 'label')

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

    return products_qs

@products_controller.get('products/{product_id}', response={
    200: ProductOut,
    404: MessageOut
})
def productDetails(request,product_id:UUID4):
    try:
        products_qs = Product.objects.get(id=product_id)

    except products_qs.DoesNotExist:
        return 404, {'detail': 'No products found'}
        

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
#-------------------------------------------------------------------------------------------------------
#  Address CRUD 

@address_controller.post('/create_address/', auth=GlobalAuth(), response={
    201: MessageOut,
    400: MessageOut
})
def create_address(request, address_in: AddressIn,city_id : UUID4):
    city = City.objects.get(id = city_id)
    user = get_object_or_404(User,id=request.auth['pk'])

    address_qs = Address(**address_in.dict(),user =user,city = city)
    address_qs.save()
    return 201, {"detail":"address created succesfully"}

# update address 
@address_controller.put('/update_address/{id}', response={200: AddressOut,400: MessageOut})
def update_address(request, id: UUID4, address_in: AddressIn):
    address = get_object_or_404(Address, id=id)
    for attr, value in address_in.dict().items():
        setattr(address, attr, value)
    address.save()
    return 200,address

# retrive address
@address_controller.get('get_address_by_id/{id}', response={
    200: AddressOut,
    404: MessageOut
})
def get_address_by_id(request, id: UUID4):
    return get_object_or_404(Address, id=id)

# get list addresses 
@address_controller.get('/list_all_addresses/',response={200:List[AddressOut],404 : MessageOut})
def list_addresses(request):
    adresses_qs = Address.objects.all()
    if adresses_qs:
        return adresses_qs

    return 404, {'detail': 'No adresses found'}


# delete address 
@address_controller.delete('delete/{id}', response={204: MessageOut})
def delete_address(request, id: UUID4):
    address = get_object_or_404(Address, id=id)
    address.delete()
    return 204, {'detail': 'deleted address sucessfully'}

#--------------------------------------------------------------------------------------------------------
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


@address_controller.post('cities', response={
    201: CitiesOut,
    400: MessageOut
})
def create_city(request, city_in: CitySchema):
    city = City(**city_in.dict())
    city.save()
    return 201, city


@address_controller.put('cities/{id}', response={
    200: CitiesOut,
    400: MessageOut
})
def update_city(request, id: UUID4, city_in: CitySchema):
    city = get_object_or_404(City, id=id)
    city.name = city_in.name
    city.save()
    return 200, city


@address_controller.delete('cities/{id}', response={
    204: MessageOut
})
def delete_city(request, id: UUID4):
    city = get_object_or_404(City, id=id)
    city.delete()
    return 204, {'detail': ''}


@order_controller.get('cart', auth = GlobalAuth(),response={
    200: List[ItemOut],
    404: MessageOut
})
def view_cart(request):
    user = get_object_or_404(User,id=request.auth['pk'])
    cart_items = Item.objects.filter(user=user, ordered=False)
    for i in cart_items :
        print(i.item_total)

    if cart_items:
        return cart_items

    return 404, {'detail': 'Your cart is empty, go shop like crazy!'}


@order_controller.post('add-to-cart', auth=GlobalAuth(),response={
    200: MessageOut,
    # 400: MessageOut
})
def add_update_cart(request, item_in: ItemCreate,size_id:str=None):
    try:
        user = get_object_or_404(User,id=request.auth['pk'])
        item = Item.objects.get(product_id=item_in.product_id, user=user)
        item.item_qty += 1
        item.save()
        if(size_id):
            user = get_object_or_404(User,id=request.auth['pk'])
            product_size = ProductSize.objects.get(id = size_id)
            item = Item.objects.get(product_id=item_in.product_id, user=user,product_size=product_size)
            item.item_qty += 1
            item.item_size = product_size
            item.save()
    except Item.DoesNotExist:
        Item.objects.create(**item_in.dict(), user=user)

    return 200, {'detail': 'Added to cart successfully'}


@order_controller.post('item/{id}/reduce-quantity',auth=GlobalAuth(), response={
    200: MessageOut,
})
def reduce_item_quantity(request, id: UUID4):
    user = get_object_or_404(User,id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=user)
    if item.item_qty <= 1:
        item.delete()
        return 200, {'detail': 'Item deleted!'}
    item.item_qty -= 1
    item.save()

    return 200, {'detail': 'Item quantity reduced successfully!'}


@order_controller.delete('/item/{id}', auth=GlobalAuth(),response={
    204: MessageOut
})
def delete_item(request, id: UUID4):
    user = get_object_or_404(User,id=request.auth['pk'])

    item = get_object_or_404(Item, id=id, user=user)
    item.delete()

    return 204, {'detail': 'Item deleted!'}


def generate_ref_code():
    return ''.join(random.sample(string.ascii_letters + string.digits, 6))


@order_controller.post('/item/{id}/increase-quantity',auth=GlobalAuth(), response={200: MessageOut,})
def increase_item_quantity(request, id: UUID4):
    user = get_object_or_404(User,id=request.auth['pk'])
    item = get_object_or_404(Item, id=id, user=user,ordered = False)
    item.item_qty += 1
    item.save()
    return 200, {'detail': 'item increased successfully'}


@order_controller.post('create-order', auth=GlobalAuth(), response={200: MessageOut,201: MessageOut})
def create_update_order(request,address_in: AddressIn):
    # set ref_code to a randomly generated 6 alphanumeric value
    ref_code = ''.join(random.sample(string.ascii_letters+string.digits,6))
    # get status 
    try :
        get_status = OrderStatus.objects.get(title = "NEW")
    except OrderStatus.DoesNotExist :
        get_status = OrderStatus.objects.create(title = "NEW",is_default = True)
    user = get_object_or_404(User,id=request.auth['pk'])
    address_qs = Address(**address_in.dict(),user =user)
    address_qs.save()
    

    # take all current items (ordered=False) 
    items_qs = Item.objects.filter(user = user,ordered = False)
    order_qs = Order.objects.filter(user=user,ordered = False).update(ordered = True)
    
    if order_qs:
        return 200, {"detail": "Order Updated Successfully"}
    else:
        order = Order.objects.create(user=user,status = get_status,ref_code =ref_code,ordered = True,address=address_qs)
        order.items.add(*items_qs)
        return 201, {"detail": "Order Created Successfully"}





@checkout_controller.post('/create/', auth=GlobalAuth(),response={200: MessageOut, 404: MessageOut})
def checkout(request, address_in: AddressIn, note : str = None):
    # crete city
    user = get_object_or_404(User,id=request.auth['pk'])
    # create address
    address_qs = Address(**address_in.dict(),user =user)
    address_qs.save()
    # get Order
    try:
        checkout = Order.objects.get(ordered=False, user=user)
    except Order.DoesNotExist:
        return 404 ,{'detail': 'Order Not Found'}
    # get note if exist 
    if note : 
        checkout.note = note

    checkout.status = OrderStatus.objects.get(title = "PROCESSING")
    checkout.total = checkout.order_total
    checkout.ordered = True
    checkout.address = address_qs
    checkout.save()
    return 200, {'detail': 'Checkout Created successfully'}



@category_controllers.get('categories', response=List[CategoryOut])
def list_categories(request):
    return Category.objects.all()


@category_controllers.get('categories/{category_id}', response=List[ProductTypeOut])
def category_products(request,category_id:UUID4):
    types = Category.objects.get(id=category_id).types.all()
    return types

@category_controllers.get('category//{category_id}/{type_id}', response=List[ProductOut])
def products_category_type(request,category_id:UUID4,type_id:UUID4):
    products = Product.objects.filter(category = Category.objects.get(id=category_id),product_type = ProductType.objects.get(id=type_id))  
    return products

