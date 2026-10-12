from fastapi import FastAPI, HTTPException, Query
from models import Product
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db
from db_models import ProductDB

app=FastAPI()

@app.get("/")
def greet():
    return "hello dd"

#searching the products
@app.get("/products/search", response_model=list[Product])
def search_products(
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(ProductDB)

    if max_price is not None:
        query = query.filter(ProductDB.price <= max_price)

    return query.all()


#fetching all products 
@app.get("/products", response_model=list[Product])
def get_all_products(db: Session=Depends(get_db)):
    return db.query(ProductDB).all()

#fetching a single product by id 
@app.get(
    "/products/{product_id}",
    response_model=Product,
    responses={404: {"description": "Product not found"}}
)
def get_product_by_id(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(ProductDB).filter(
        ProductDB.product_id == product_id
    ).first()
    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product Not Found"
        )
    return product


#creating a product
@app.post("/products",status_code=201,response_model=Product,
    responses={409: {"description": "A product with this ID already exists"}}
)
def add_product(product: Product, db: Session = Depends(get_db)):
    existing_product = db.query(ProductDB).filter(
        ProductDB.product_id == product.product_id
    ).first()
    if existing_product:
        raise HTTPException(
            status_code=409,
            detail="A product with this ID already exists"
        )
    new_product = ProductDB(
        name=product.name,
        price=product.price,
        product_id=product.product_id,
        description=product.description,
        quantity=product.quantity
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

#update the product 

@app.put("/products/{product_id}", response_model=Product)
def update_by_id(
    product_id: int,
    update_product: Product,
    db: Session = Depends(get_db)
):
    if update_product.product_id != product_id:
        raise HTTPException(
            status_code=400,
            detail="Product ID in the body must match the URL"
        )

    existing_product = db.query(ProductDB).filter(
        ProductDB.product_id == product_id
    ).first()

    if existing_product is None:
        raise HTTPException(
            status_code=404,
            detail="Product Not Found"
        )

    existing_product.name = update_product.name
    existing_product.price = update_product.price
    existing_product.description = update_product.description
    existing_product.quantity = update_product.quantity

    db.commit()
    db.refresh(existing_product)

    return existing_product



#delete the product
@app.delete("/products/{product_id}", status_code=204)
def delete_product_by_id(
    product_id: int,
    db: Session = Depends(get_db)
):
        product=db.query(ProductDB).filter(
            ProductDB.product_id==product_id
        ).first()
        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product Not Found"
            )
        db.delete(product)
        db.commit()
        return
    


    
