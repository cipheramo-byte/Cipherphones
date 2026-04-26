from flask import Flask, render_template, redirect, url_for, request, session
from config import Config
from models import db, User, Product, Cart, Order
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# HOME
@app.route("/")
def home():
    products = Product.query.all()
    return render_template("index.html", products=products, user=current_user)

# AUTH
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"])
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/")

# CART
@app.route("/add/<int:id>")
@login_required
def add_to_cart(id):
    db.session.add(Cart(user_id=current_user.id, product_id=id))
    db.session.commit()
    return redirect("/")

@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    products = [Product.query.get(i.product_id) for i in items]
    total = sum(p.price for p in products)
    return render_template("cart.html", products=products, total=total)

# PAYMENT
@app.route("/checkout")
@login_required
def checkout():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    total = sum(Product.query.get(i.product_id).price for i in items)
    return render_template("pay.html", total=total, public_key=Config.PAYSTACK_PUBLIC)

@app.route("/verify/<ref>")
@login_required
def verify(ref):
    url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {"Authorization": f"Bearer {Config.PAYSTACK_SECRET}"}

    res = requests.get(url, headers=headers).json()

    if res["data"]["status"] == "success":
        items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(Product.query.get(i.product_id).price for i in items)

        db.session.add(Order(user_id=current_user.id, total=total))
        Cart.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()

        return "Payment successful!"
    return "Payment failed"

# ADMIN
def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect("/")

@app.route("/admin")
@login_required
def admin():
    admin_required()
    return render_template("admin.html",
        products=Product.query.all(),
        orders=Order.query.all()
    )

@app.route("/admin/add", methods=["GET","POST"])
@login_required
def add():
    admin_required()
    if request.method == "POST":
        db.session.add(Product(
            name=request.form["name"],
            price=request.form["price"],
            image=request.form["image"]
        ))
        db.session.commit()
        return redirect("/admin")
    return render_template("add_product.html")

@app.route("/admin/delete/<int:id>")
@login_required
def delete(id):
    admin_required()
    db.session.delete(Product.query.get(id))
    db.session.commit()
    return redirect("/admin")

# RUN
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()