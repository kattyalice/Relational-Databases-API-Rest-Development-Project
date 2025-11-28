from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from flask_marshmallow import Marshmallow
from datetime import date
from typing import List
from marshmallow import ValidationError, fields
from sqlalchemy import select, delete

#==================== App Initialization ====================#
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Simelia5!4@localhost/ecommerce_api'
db = SQLAlchemy(app)
ma = Marshmallow(app)

#==================== Models ====================#
class Base(DeclarativeBase):
    pass

# User Table
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    email: Mapped[str] = mapped_column(db.String(100), unique=True)
    address: Mapped[str] = mapped_column(db.String(200))
    orders: Mapped[List["Orders"]] = db.relationship(back_populates='user')
 
# Order_Product Assocation Table
order_products = db.Table(
    "order_products", 
    Base.metadata,
    db.Column('order_id', db.ForeignKey('orders.id')),
    db.Column('product_id', db.ForeignKey('products.id'))
)

# Order Table
class Orders(Base):
    __tablename__ = 'Orders'
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    user_id: Mapped[int] = mapped_column(db.ForeignKey('users.id'))
    products: Mapped[List['Products']] = db.relationship(secondary=order_products, back_populates='orders')
    user: Mapped['User'] = db.relationship(back_populates='orders')
 
 # Product Table   
class Products(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(db.String(100), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    orders: Mapped[List['Orders']] = db.relationship(secondary=order_products, back_populates='products')
    
# Initialize the database
with app.app_context():
    Base.metadata.create_all(db.engine)
    
    
#==================== Schemas ====================#
# The layout of how a database is organized
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
    
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Products
        
class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Orders
        include_fk = True
        
user_schema = UserSchema()
users_schema = UserSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

#==================== Routes & Endpoints ====================#
@app.route('/')
def home():
    return "Home"

# User Endpoints (CRUD)
# Create a new user
@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
        new_user = User(name=user_data['name'], email=user_data['email'], address=user_data['address'])
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"Message": "New user added successfully!",
                        "User": user_schema.dump(new_user)}), 201
    except ValidationError as e:
        db.session.rollback()
        return jsonify(e.messages), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Retrieve all users
@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()
    return users_schema.jsonify(users)

# Retrieve a user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    query = select(User).where(User.id == id)
    user = db.session.execute(query).scalars().first()
    
    if user is None:
        return jsonify({"Error": "User not found"}), 404
    
    return user_schema.jsonify(user)

    
# Update a user by ID
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    query = select(User).where(User.id == id)
    user = db.session.execute(query).scalars().first()
    
    if user is None:
        return jsonify({"Error": "User not found"}), 404
    
    data = request.json
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.address = data.get('address', user.address)
    
    db.session.commit()
    return jsonify(user_schema.dump(user)), 200

# Delete a user by ID
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    query = select(User).where(User.id == id)
    user = db.session.execute(query).scalars().first()
    
    if user is None:
        return jsonify({"Error": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"Message": "User deleted successfully!"})

    
# Products Endpoints (CRUD)
# Create Product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
        new_product = Products(product_name=product_data['product_name'], price=product_data['price'])
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"Messages": "New product added!",
                    "product": product_schema.dump(new_product)}), 201
    except ValidationError as e:
        return jsonify(e.messages), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    
    
    
# Get all products
@app.route('/products', methods=["GET"])
def get_products():
    query = select(Products)
    products = db.session.execute(query).scalars().all()
    return products_schema.jsonify(products)

# Get product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    query = select(Products).where(Products.id == id)
    product = db.session.execute(query).scalars().first()
    
    if product is None:
        return jsonify({"Error": "Product not found"}), 404
    
    return product_schema.jsonify(product)

# Update a product by ID
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    query = select(Products).where(Products.id == id)
    product = db.session.execute(query).scalars().first()
    
    if product is None:
        return jsonify({"Error": "Product not found"}), 404

    data = request.json
    product.product_name = data.get('product_name', product.product_name)
    product.price = data.get('price', product.price)
    
    db.session.commit()
    return jsonify(product_schema.dump(product)), 200

# Delete a product by ID
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    query = select(Products).where(Products.id == id)
    product = db.session.execute(query).scalars().first()
    
    if product is None:
        return jsonify({"Error": "Product not found"}), 404
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"Message": "Product deleted successfully"})

# Order Endpoints (CRUD)
# Create Order
@app.route('/orders', methods=['POST'])
def create_order():
    user = db.session.get(User, request.json.get('user_id'))
    if user is None:
        return jsonify({"Error": "User not found"}), 404
    
    try:
        order_data = order_schema.load(request.json)
        new_order = Orders(user_id=order_data['user_id'], order_date=order_data['order_date'])
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"Messages": "New order created!",
                    "order": order_schema.dump(new_order)}), 201
    except ValidationError as e:
        return jsonify(e.messages), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    
# Get all orders for a user
@app.route('/orders/user/<user_id>', methods=['GET'])
def user_orders(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"Error": "User not found"}), 404
    
    query = select(Orders).where(Orders.user_id == user_id)
    orders = db.session.execute(query).scalars().all()
    return orders_schema.jsonify(orders), 200

# Get all products for an order
@app.route('/orders/<order_id>/products', methods=['GET'])
def products_ordered(order_id):
     order = db.session.get(Orders, order_id)
     if order is None:
         return jsonify({"Error": "No orders found"}), 404
     products_list = order.products
     return products_schema.jsonify(products_list), 200

# Add a product to an order (prevent duplicates)
@app.route('/orders/<order_id>/add_product/<product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = db.session.get(Orders, order_id)
    if order is None:
        return jsonify({"Error": "Order not found"}), 404
    
    product = db.session.get(Products, product_id)
    if product is None:
        return jsonify({"Error": "No product found"}), 404
    
    if product in order.products:
        return jsonify({"Error": "Product already on order"}), 409
    
    try:
        order.products.append(product)
        db.session.commit()
        return jsonify(order_schema.dump(order)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"Error": str(e)}), 400

# Remove a product from an order
@app.route('/orders/<order_id>/remove_product/<product_id>', methods=['DELETE'])
def remove_from_order(order_id, product_id):
    order = db.session.get(Orders, order_id)
    if order is None:
        return jsonify({"Error": "Order not found"}), 404
    
    product = db.session.get(Products, product_id)
    if product is None:
        return jsonify({"Error": "Product not found"}), 404
    
    if product not in order.products:
        return jsonify({"Error": "Product not on order"}), 409
    
    try:
        order.products.remove(product)
        db.session.commit()
        return jsonify(order_schema.dump(order)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"Error": str(e)}), 400