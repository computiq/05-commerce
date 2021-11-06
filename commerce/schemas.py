from typing import List

from ninja import ModelSchema, Schema
from ninja.orm import create_schema
from pydantic import UUID4

from commerce.models import Product, Merchant, Address, Order, OrderStatus


class MessageOut(Schema):
    detail: str


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


class AddressSchema(Schema):
    work_address:bool = False
    address1:str
    address2:str
    city: CitiesOut
    phone:str

class AddressOut(UUIDSchema, AddressSchema):
    user_id:UUID4



class AddressCreate(Schema):
    work_address: bool
    address1: str
    address2: str
    city_id: UUID4
    phone: str
   



class orderstatus(UUIDSchema):
    pass



class OrderSchema(Schema):
    address_id:UUID4=None
    note:str=None
    total:str
    status:orderstatus
    ref_code:str
    ordered:bool


class OrderOut(UUIDSchema, OrderSchema):
    user_id:UUID4


class checkout(Schema):
    address_id:UUID4
    note:str
    status:UUID4
    ordered:bool