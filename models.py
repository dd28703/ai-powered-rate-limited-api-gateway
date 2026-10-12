from pydantic import BaseModel
class Product(BaseModel):
    name: str 
    price: float 
    product_id: int
    description: str
    quantity: int
