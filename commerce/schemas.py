from typing import List
from ninja import ModelSchema, Schema
from pydantic import UUID4
from django.contrib.auth import get_user_model
from pydantic.networks import EmailStr
from commerce.models import Product, Merchant
User = get_user_model()






class UUIDSchema(Schema):
    id: UUID4


# ProductSchemaOut = create_schema(Product, depth=2)

class VendorOut(UUIDSchema):
    name: str
    image: str


class LabelOut(UUIDSchema):
    name: str


class MerchantOut(ModelSchema):
    class Config:
        model = Merchant
        model_fields = ['id', 'name']


class CategoryOut(UUIDSchema):
    name: str
    description: str
    image: str
    children: List['CategoryOut'] = None


CategoryOut.update_forward_refs()


class ProductOut(ModelSchema):
    vendor: VendorOut
    label: LabelOut
    merchant: MerchantOut
    category: CategoryOut

    class Config:
        model = Product
        model_fields = ['id',
                        'name',
                        'description',
                        'qty',
                        'price',
                        'discounted_price',
                        'vendor',
                        'category',
                        'label',
                        'merchant',

                        ]


# class ProductManualSchemaOut(Schema):
#     pass


class CitySchema(Schema):
    name: str


class CitiesOut(CitySchema, UUIDSchema):
    pass


class ItemSchema(Schema):
    # user:
    product: ProductOut
    item_qty: int
    ordered: bool


class ItemCreate(Schema):
    product_id: UUID4
    item_qty: int


class ItemOut(UUIDSchema, ItemSchema):
    pass
class Orderstatusschema(Schema):
    title:      str
    is_default: bool

class Addressout(Schema):
    address1: str
    phone: str
    city_id: UUID4
    work_address: bool
    address2: str = None

class Addresslist(Addressout, UUIDSchema):
    user_id : UUID4
class OrderStatus(Schema):
    title: str
class OrderCreate(Schema):
    items: List[UUID4]
    address: UUID4
    note: str 

