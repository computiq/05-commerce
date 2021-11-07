from typing import List
from ninja import ModelSchema, Schema
from pydantic import UUID4
from commerce.models import Product, Merchant


class UUIDSchema(Schema):
    id: UUID4


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
    vendor: VendorOut = None
    label: LabelOut = None
    merchant: MerchantOut = None
    category: CategoryOut = None

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



class CitySchema(Schema):
    name: str


class CitiesOut(CitySchema, UUIDSchema):
    pass


class ItemSchema(Schema):
    product: ProductOut
    item_qty: int
    ordered: bool


class ItemCreate(Schema):
    product_id: UUID4
    item_qty: int


class ItemOut(UUIDSchema, ItemSchema):
    pass


class AddressSchema(Schema):
    work_address: bool
    address1: str
    address2: str
    city: UUID4
    phone: int


# i'll edit this soon #

# class AddressUpdate(Schema):
#     work_address: bool
#     address1: str
#     address2: str
#     city: CitySchema
#     phone: int


class AddressOut(AddressSchema, UUIDSchema):
    city: CitiesOut


class CheckoutSchema(Schema):
    note: str = None
    address: UUID4

