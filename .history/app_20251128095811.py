from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Table, Column, String, Integer, Float, ForeignKey, Date
from sqlalchemy import select
from marshmallow import ValidationError
from datetime import date
from typing import List

#==================== App Initialization ====================#
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Simelia5!4@localhost/ecommerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)     # used ONLY for engine/session management
ma = Marshmallow(app)


#==================== Declarative Base ====================#
class Base(DeclarativeBase):
    pass


#==================== Models (Pure SQLAlchemy) ====================#

# --- Association Table ---
order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True),
)


# --- User Table ---
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    address: Mapped[str] = mapped_column(String(200))

    orders: Mapped[List["Orders"]] = relationship(back_populates="user")


# --- Orders Table ---
class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="orders")
    products: Mapped[List["Products"]] = relationship(
        secondary=order_products,
        back_populates="orders"
    )


# --- Products Table ---
class Products(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    orders: Mapped[List["Orders"]] = relationship(
        secondary=order_products,
        back_populates="products"
    )


#==================== Create Tables ====================#
with app.app_context():
    Base.metadata.create_all(db.engine)


#==================== Schemas ====================#
class UserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = User
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    email = ma.auto_field()
    address = ma.auto_field()


class ProductSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Products
        load_instance = True

    id = ma.auto_field()
    product_name = ma.auto_field()
    price = ma.auto_field()


class OrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Orders
        load_instance = True
        include_fk = True

    id = ma.auto_field()
    order_date = ma.auto_field()
    user_id = ma.auto_field()


user_schema = UserSchema()
users_schema = UserSchema(many=True)

product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)


#==================== Routes ====================#
@app.route('/')
def home():
    return "E-commerce API Working!"


#==================== USERS CRUD ====================#
@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = user_schema.load(request.json)
        new_user = User(**request.json)
        db.session.add(new_user)
        db.session.commit()
        return user_schema.jsonify(new_user), 201
    except ValidationError as e:
        return jsonify(e.messages), 400


@app.route('/users', methods=['GET'])
def get_users():
    users = db.session.execute(select(User)).scalars().all()
    return users_schema.jsonify(users)


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"Error": "User not found"}), 404
    return user_schema.jsonify(user)


@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"Error": "User not found"}), 404

    data = request.json
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.address = data.get("address", user.address)

    db.session.commit()
    return user_schema.jsonify(user)


@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"Error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"Message": "User deleted"})


#==================== PRODUCTS CRUD ====================#
@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
        new_product = Products(**request.json)
        db.session.add(new_product)
        db.session.commit()
        return product_schema.jsonify(new_product), 201
    except ValidationError as e:
        return jsonify(e.messages), 400


@app.route('/products', methods=['GET'])
def get_products():
    products = db.session.execute(select(Products)).scalars().all()
    return products_schema.jsonify(products)


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({"Error": "Product not found"}), 404
    return product_schema.jsonify(product)


@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({"Error": "Product not found"}), 404

    data = request.json
    product.product_name = data.get("product_name", product.product_name)
    product.price = data.get("price", product.price)

    db.session.commit()
    return product_schema.jsonify(product)


@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Products, id)
    if not product:
        return jsonify({"Error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"Message": "Product deleted"})


#==================== ORDERS ====================#
@app.route('/orders', methods=['POST'])
def create_order():
    user = db.session.get(User, request.json.get("user_id"))
    if not user:
        return jsonify({"Error": "User not found"}), 404

    new_order = Orders(**request.json)
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201


@app.route('/orders/user/<int:user_id>', methods=['GET'])
def user_orders(user_id):
    orders = db.session.execute(select(Orders).where(Orders.user_id == user_id)).scalars().all()
    return orders_schema.jsonify(orders)


@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_order_products(order_id):
    order = db.session.get(Orders, order_id)
    if not order:
        return jsonify({"Error": "Order not found"}), 404
    return products_schema.jsonify(order.products)


@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if not order:
        return jsonify({"Error": "Order not found"}), 404
    if not product:
        return jsonify({"Error": "Product not found"}), 404
    if product in order.products:
        return jsonify({"Error": "Product already added"}), 409

    order.products.append(product)
    db.session.commit()
    return order_schema.jsonify(order)


@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product(order_id, product_id):
    order = db.session.get(Orders, order_id)
    product = db.session.get(Products, product_id)

    if not order:
        return jsonify({"Error": "Order not found"}), 404
    if not product:
        return jsonify({"Error": "Product not found"}), 404
    if product not in order.products:
        return jsonify({"Error": "Product not in order"}), 409

    order.products.remove(product)
    db.session.commit()
    return order_schema.jsonify(order)


#==================== Run Server ====================#
if __name__ == '__main__':
    app.run(debug=True)
