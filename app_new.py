import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, func, desc, inspect, text

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
database_url = os.environ.get("DATABASE_URL", "sqlite:///coffeelink.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
if database_url.startswith("postgresql://") and "sslmode=" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Silakan login untuk melanjutkan."
login_manager.login_message_category = "warning"

# Add custom template filters
@app.template_filter('currency')
def currency_filter(value, currency='USD'):
    """Format number as currency"""
    if value is None:
        return '-'
    return f"{currency} {value:,.2f}"

@app.template_filter('number')
def number_filter(value, decimals=0):
    """Format number with commas"""
    if value is None:
        return '-'
    if decimals == 0:
        return f"{value:,.0f}"
    return f"{value:,.{decimals}f}"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="buyer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Farmer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    village = db.Column(db.String(120), nullable=False)
    region = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40))
    email = db.Column(db.String(150))
    certification = db.Column(db.String(100), default="Belum ada")
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Buyer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(150), nullable=False)
    contact_person = db.Column(db.String(120), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(40))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CoffeeProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    variety = db.Column(db.String(80), nullable=False)
    process = db.Column(db.String(80), nullable=False)
    grade = db.Column(db.String(40), nullable=False)
    stock_kg = db.Column(db.Float, nullable=False, default=0)
    price_per_kg = db.Column(db.Float, nullable=False, default=0)
    origin = db.Column(db.String(120), nullable=False)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmer.id"), nullable=False)
    farmer = db.relationship("Farmer", backref="products")
    # New fields for marketplace
    harvest_year = db.Column(db.String(20))
    moisture = db.Column(db.Float)
    cupping_score = db.Column(db.Float)
    cupping_notes = db.Column(db.Text)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    additional_images = db.Column(db.Text)  # JSON array
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_additional_images(self):
        if self.additional_images:
            try:
                import json
                return json.loads(self.additional_images)
            except:
                return []
        return []


class ExportOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(30), unique=True, nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("coffee_product.id"), nullable=False)
    quantity_kg = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(5), default="USD")
    destination = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), default="Menunggu konfirmasi")
    order_date = db.Column(db.Date, default=datetime.utcnow().date)
    buyer = db.relationship("Buyer", backref="orders")
    product = db.relationship("CoffeeProduct", backref="orders")


class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("export_order.id"), unique=True, nullable=False)
    carrier = db.Column(db.String(120), nullable=False)
    tracking_number = db.Column(db.String(100))
    departure_port = db.Column(db.String(120), nullable=False)
    destination_port = db.Column(db.String(120), nullable=False)
    ship_date = db.Column(db.Date)
    estimated_arrival = db.Column(db.Date)
    status = db.Column(db.String(30), default="Persiapan")
    notes = db.Column(db.Text)
    order = db.relationship("ExportOrder", backref=db.backref("shipment", uselist=False))


class Inquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("buyer.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("coffee_product.id"), nullable=False)
    quantity_kg = db.Column(db.Float)
    message = db.Column(db.Text, nullable=False)
    incoterms = db.Column(db.String(20))
    timeline = db.Column(db.String(50))
    status = db.Column(db.String(30), default="New")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    buyer = db.relationship("Buyer", backref="inquiries")
    product = db.relationship("CoffeeProduct", backref="inquiries")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def farmer_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return login_manager.unauthorized()
        if current_user.role not in ("farmer", "admin"):
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "buyer")
        if role not in ("buyer", "farmer"):
            role = "buyer"
        if not name or not email or len(password) < 6:
            flash("Lengkapi data. Password minimal 6 karakter.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar.", "danger")
        else:
            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            if role == "buyer":
                db.session.add(Buyer(company=name, contact_person=name, country="Belum diisi", email=email))
            elif role == "farmer":
                db.session.add(Farmer(name=name, village="Belum diisi", region="Belum diisi", email=email))
            db.session.commit()
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("login"))
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for("dashboard"))
        flash("Email atau password salah.", "danger")
    return render_template("auth.html", mode="login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    stats = {
        "farmers": Farmer.query.count(),
        "buyers": Buyer.query.count(),
        "products": CoffeeProduct.query.count(),
        "orders": ExportOrder.query.count(),
        "shipments": Shipment.query.count(),
        "revenue": db.session.query(db.func.coalesce(db.func.sum(ExportOrder.total_value), 0)).scalar(),
        "total_kg": db.session.query(db.func.coalesce(db.func.sum(ExportOrder.quantity_kg), 0)).scalar()
    }
    recent_orders = ExportOrder.query.order_by(ExportOrder.id.desc()).limit(6).all()

    # Low stock products
    low_stock_products = CoffeeProduct.query.filter(
        CoffeeProduct.stock_kg > 0,
        CoffeeProduct.stock_kg < 100
    ).order_by(CoffeeProduct.stock_kg).limit(5).all()

    return render_template("dashboard_new.html", stats=stats, recent_orders=recent_orders, low_stock_products=low_stock_products)


# Marketplace routes
@app.route("/marketplace")
def marketplace():
    # Get filter parameters
    q = request.args.get('q', '').strip()
    selected_origins = request.args.getlist('origin')
    selected_varieties = request.args.getlist('variety')
    selected_processes = request.args.getlist('process')
    selected_grades = request.args.getlist('grade')
    filter_args = request.args.to_dict(flat=False)
    filter_args.pop('sort', None)
    filter_args.pop('page', None)
    min_score = request.args.get('min_score', type=float)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock', type=int)
    featured = request.args.get('featured', type=int)
    active_filter_count = (
        len(selected_origins) + len(selected_varieties) +
        len(selected_processes) + len(selected_grades) +
        int(bool(min_score or min_price or max_price or in_stock or featured))
    )
    sort_by = request.args.get('sort', 'newest')
    sort_label = {
        'newest': 'Newest arrivals',
        'price_asc': 'Price: Low to High',
        'price_desc': 'Price: High to Low',
        'cupping_desc': 'Cupping Score: Highest',
        'stock_desc': 'Most Available',
    }.get(sort_by, 'Newest arrivals')
    page = request.args.get('page', 1, type=int)
    view_mode = request.args.get('view', 'grid')

    # Build query
    query = CoffeeProduct.query.join(Farmer)

    if q:
        query = query.filter(or_(
            CoffeeProduct.name.ilike(f'%{q}%'),
            CoffeeProduct.origin.ilike(f'%{q}%'),
            CoffeeProduct.variety.ilike(f'%{q}%')
        ))

    if selected_origins:
        query = query.filter(CoffeeProduct.origin.in_(selected_origins))
    if selected_varieties:
        query = query.filter(CoffeeProduct.variety.in_(selected_varieties))
    if selected_processes:
        query = query.filter(CoffeeProduct.process.in_(selected_processes))
    if selected_grades:
        query = query.filter(CoffeeProduct.grade.in_(selected_grades))
    if min_score:
        query = query.filter(CoffeeProduct.cupping_score >= min_score)
    if min_price:
        query = query.filter(CoffeeProduct.price_per_kg >= min_price)
    if max_price:
        query = query.filter(CoffeeProduct.price_per_kg <= max_price)
    if in_stock:
        query = query.filter(CoffeeProduct.stock_kg > 0)
    if featured:
        query = query.filter(CoffeeProduct.featured == True)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(CoffeeProduct.price_per_kg.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(CoffeeProduct.price_per_kg.desc())
    elif sort_by == 'cupping_desc':
        query = query.order_by(CoffeeProduct.cupping_score.desc().nullslast())
    elif sort_by == 'stock_desc':
        query = query.order_by(CoffeeProduct.stock_kg.desc())
    else:  # newest
        query = query.order_by(CoffeeProduct.created_at.desc())

    # Get filter options for template
    origins = db.session.query(CoffeeProduct.origin).distinct().all()
    origins = [o[0] for o in origins if o[0]]
    varieties = db.session.query(CoffeeProduct.variety).distinct().all()
    varieties = [v[0] for v in varieties if v[0]]
    processes = db.session.query(CoffeeProduct.process).distinct().all()
    processes = [p[0] for p in processes if p[0]]
    grades = db.session.query(CoffeeProduct.grade).distinct().all()
    grades = [g[0] for g in grades if g[0]]

    # Pagination
    per_page = 12
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    return render_template("marketplace.html",
        products=products,
        pagination=pagination,
        origins=origins,
        varieties=varieties,
        processes=processes,
        grades=grades,
        selected_origins=selected_origins,
        selected_varieties=selected_varieties,
        selected_processes=selected_processes,
        selected_grades=selected_grades,
        sort_by=sort_by,
        sort_label=sort_label,
        view_mode=view_mode,
        min_score=min_score,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        featured=featured,
        filter_args=filter_args,
        active_filter_count=active_filter_count
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = db.session.get(CoffeeProduct, product_id)
    if not product:
        abort(404)
    return render_template("product_detail.html", product=product)


@app.route("/inquiries")
@login_required
def inquiries():
    if current_user.role == 'buyer':
        buyer = Buyer.query.filter_by(email=current_user.email).first()
        if buyer:
            inquiries_list = Inquiry.query.filter_by(buyer_id=buyer.id).order_by(Inquiry.created_at.desc()).all()
        else:
            inquiries_list = []
    elif current_user.role == 'farmer':
        farmer = Farmer.query.filter_by(email=current_user.email).first()
        if farmer:
            product_ids = [p.id for p in farmer.products]
            inquiries_list = Inquiry.query.filter(Inquiry.product_id.in_(product_ids)).order_by(Inquiry.created_at.desc()).all()
        else:
            inquiries_list = []
    else:
        inquiries_list = Inquiry.query.order_by(Inquiry.created_at.desc()).all()

    return render_template("inquiries.html", inquiries=inquiries_list)


@app.route("/inquiries/new", methods=["POST"])
@login_required
def create_inquiry():
    if current_user.role != 'buyer':
        abort(403)

    buyer = Buyer.query.filter_by(email=current_user.email).first()
    if not buyer:
        flash("Buyer profile not found.", "danger")
        return redirect(url_for('marketplace'))

    product_id = request.form.get('product_id', type=int)
    product = db.session.get(CoffeeProduct, product_id)
    if not product:
        abort(404)

    inquiry = Inquiry(
        buyer_id=buyer.id,
        product_id=product.id,
        quantity_kg=request.form.get('quantity_kg', type=float),
        message=request.form.get('message', ''),
        incoterms=request.form.get('incoterms', 'FOB'),
        timeline=request.form.get('timeline', 'asap'),
        status='New'
    )
    db.session.add(inquiry)
    db.session.commit()
    flash("Inquiry sent successfully!", "success")
    return redirect(url_for('inquiries'))


# Master data routes (admin only)
MASTER_CONFIG = {
    "farmers": {
        "title": "Data Petani", "model": Farmer,
        "fields": [("name", "Nama petani", "text"), ("village", "Desa", "text"),
                   ("region", "Kabupaten / Provinsi", "text"), ("phone", "Nomor telepon", "text"),
                   ("email", "Email", "email"), ("certification", "Sertifikasi", "text"),
                   ("description", "Deskripsi", "textarea")],
        "columns": ["name", "village", "region", "phone", "certification"]
    },
    "buyers": {
        "title": "Data Pembeli", "model": Buyer,
        "fields": [("company", "Nama perusahaan", "text"), ("contact_person", "Kontak person", "text"),
                   ("country", "Negara", "text"), ("email", "Email", "email"), ("phone", "Telepon", "text")],
        "columns": ["company", "contact_person", "country", "email", "phone"]
    },
    "products": {
        "title": "Data Produk Kopi", "model": CoffeeProduct,
        "fields": [("name", "Nama produk", "text"), ("variety", "Varietas", "text"),
                   ("process", "Proses", "text"), ("grade", "Grade", "text"),
                   ("stock_kg", "Stok (kg)", "number"), ("price_per_kg", "Harga per kg (USD)", "number"),
                   ("origin", "Asal kopi", "text"), ("farmer_id", "Petani", "farmer"),
                   ("harvest_year", "Tahun panen", "text"), ("moisture", "Kelembaban (%)", "number"),
                   ("cupping_score", "Cupping Score", "number"), ("cupping_notes", "Catatan Cupping", "textarea"),
                   ("description", "Deskripsi", "textarea"), ("image_url", "URL Gambar", "text"),
                   ("featured", "Unggulan", "checkbox")],
        "columns": ["name", "variety", "process", "grade", "stock_kg", "price_per_kg", "origin", "cupping_score"]
    }
}


@app.route("/master/<kind>")
@login_required
@admin_required
def master_list(kind):
    cfg = MASTER_CONFIG.get(kind)
    if not cfg:
        abort(404)
    records = cfg["model"].query.order_by(cfg["model"].id.desc()).all()
    return render_template("master_list.html", kind=kind, cfg=cfg, records=records)


@app.route("/master/<kind>/new", methods=["GET", "POST"])
@app.route("/master/<kind>/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def master_form(kind, record_id=None):
    cfg = MASTER_CONFIG.get(kind)
    if not cfg:
        abort(404)
    record = db.session.get(cfg["model"], record_id) if record_id else None
    if record_id and not record:
        abort(404)
    if request.method == "POST":
        try:
            for field, label, field_type in cfg["fields"]:
                value = request.form.get(field, "").strip()
                if field_type == "number":
                    value = float(value or 0)
                elif field_type == "farmer":
                    value = int(value)
                elif field_type == "checkbox":
                    value = bool(request.form.get(field))
                elif field_type == "textarea":
                    value = request.form.get(field, "")
                setattr(record, field, value) if record else None
            if not record:
                record = cfg["model"]()
                for field, label, field_type in cfg["fields"]:
                    value = request.form.get(field, "").strip()
                    if field_type == "number":
                        value = float(value or 0)
                    elif field_type == "farmer":
                        value = int(value)
                    elif field_type == "checkbox":
                        value = bool(request.form.get(field))
                    elif field_type == "textarea":
                        value = request.form.get(field, "")
                    setattr(record, field, value)
                db.session.add(record)
            db.session.commit()
            flash("Data berhasil disimpan.", "success")
            return redirect(url_for("master_list", kind=kind))
        except (ValueError, TypeError):
            db.session.rollback()
            flash("Periksa kembali data yang dimasukkan.", "danger")
    farmers = Farmer.query.order_by(Farmer.name).all() if kind == "products" else []
    return render_template("master_form.html", kind=kind, cfg=cfg, record=record, farmers=farmers)


@app.route("/master/<kind>/<int:record_id>/delete", methods=["POST"])
@login_required
@admin_required
def master_delete(kind, record_id):
    cfg = MASTER_CONFIG.get(kind)
    if not cfg:
        abort(404)
    record = db.session.get(cfg["model"], record_id)
    if not record:
        abort(404)
    try:
        db.session.delete(record)
        db.session.commit()
        flash("Data berhasil dihapus.", "success")
    except Exception:
        db.session.rollback()
        flash("Data tidak dapat dihapus karena sudah digunakan pada transaksi.", "danger")
    return redirect(url_for("master_list", kind=kind))


@app.route("/transactions")
@login_required
def transactions():
    query = ExportOrder.query
    if current_user.role != "admin":
        buyer = Buyer.query.filter_by(email=current_user.email).first()
        query = query.filter_by(buyer_id=buyer.id) if buyer else query.filter_by(id=-1)
    orders = query.order_by(ExportOrder.id.desc()).all()
    return render_template("transactions.html", orders=orders)


@app.route("/transactions/new", methods=["GET", "POST"])
@login_required
def transaction_new():
    if current_user.role == "farmer":
        abort(403)
    buyers = Buyer.query.order_by(Buyer.company).all()
    products = CoffeeProduct.query.order_by(CoffeeProduct.name).all()
    if request.method == "POST":
        try:
            buyer_id = int(request.form["buyer_id"])
            product_id = int(request.form["product_id"])
            qty = float(request.form["quantity_kg"])
            buyer = db.session.get(Buyer, buyer_id)
            product = db.session.get(CoffeeProduct, product_id)
            if not buyer or not product or qty <= 0 or qty > product.stock_kg:
                raise ValueError()
            if current_user.role != "admin":
                own_buyer = Buyer.query.filter_by(email=current_user.email).first()
                if not own_buyer or own_buyer.id != buyer.id:
                    abort(403)
            order = ExportOrder(
                order_code="CL-" + datetime.utcnow().strftime("%y%m%d%H%M%S"),
                buyer_id=buyer.id, product_id=product.id, quantity_kg=qty,
                unit_price=product.price_per_kg, total_value=qty * product.price_per_kg,
                currency=request.form.get("currency", "USD"),
                destination=request.form.get("destination", buyer.country),
                status="Menunggu konfirmasi"
            )
            product.stock_kg -= qty
            db.session.add(order)
            db.session.commit()
            flash("Pesanan ekspor berhasil dibuat.", "success")
            return redirect(url_for("transactions"))
        except (ValueError, KeyError):
            db.session.rollback()
            flash("Data pesanan tidak valid atau stok tidak mencukupi.", "danger")
    return render_template("transaction_form.html", buyers=buyers, products=products)


@app.route("/transactions/<int:order_id>/status", methods=["POST"])
@login_required
@admin_required
def transaction_status(order_id):
    order = db.session.get(ExportOrder, order_id)
    if not order:
        abort(404)
    order.status = request.form.get("status", order.status)
    db.session.commit()
    flash("Status pesanan diperbarui.", "success")
    return redirect(url_for("transactions"))


@app.route("/shipments")
@login_required
@admin_required
def shipments():
    records = Shipment.query.order_by(Shipment.id.desc()).all()
    return render_template("shipments.html", records=records)


@app.route("/shipments/new", methods=["GET", "POST"])
@login_required
@admin_required
def shipment_new():
    orders = ExportOrder.query.filter(~ExportOrder.id.in_(db.session.query(Shipment.order_id))).all()
    if request.method == "POST":
        try:
            record = Shipment(
                order_id=int(request.form["order_id"]),
                carrier=request.form["carrier"].strip(),
                tracking_number=request.form.get("tracking_number", "").strip(),
                departure_port=request.form["departure_port"].strip(),
                destination_port=request.form["destination_port"].strip(),
                ship_date=datetime.strptime(request.form["ship_date"], "%Y-%m-%d").date() if request.form.get("ship_date") else None,
                estimated_arrival=datetime.strptime(request.form["estimated_arrival"], "%Y-%m-%d").date() if request.form.get("estimated_arrival") else None,
                status=request.form.get("status", "Persiapan"),
                notes=request.form.get("notes", "").strip()
            )
            db.session.add(record)
            db.session.commit()
            flash("Data pengiriman berhasil dibuat.", "success")
            return redirect(url_for("shipments"))
        except Exception:
            db.session.rollback()
            flash("Gagal menyimpan pengiriman. Periksa data dan pesanan.", "danger")
    return render_template("shipment_form.html", orders=orders)


@app.route("/shipments/<int:shipment_id>/status", methods=["POST"])
@login_required
@admin_required
def shipment_status(shipment_id):
    record = db.session.get(Shipment, shipment_id)
    if not record:
        abort(404)
    record.status = request.form.get("status", record.status)
    db.session.commit()
    flash("Status pengiriman diperbarui.", "success")
    return redirect(url_for("shipments"))


@app.route("/reports")
@login_required
@admin_required
def reports():
    orders = ExportOrder.query.order_by(ExportOrder.order_date.desc()).all()
    total_kg = sum(o.quantity_kg for o in orders)
    total_value = sum(o.total_value for o in orders)
    return render_template("reports.html", orders=orders, total_kg=total_kg, total_value=total_value)


@app.errorhandler(403)
def forbidden(_):
    return render_template("error.html", code=403, message="Anda tidak memiliki akses ke halaman ini."), 403


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", code=404, message="Halaman atau data tidak ditemukan."), 404


def initialize_database():
    with app.app_context():
        legacy_columns = {
            "farmer": {"description": "TEXT"},
            "coffee_product": {
                "harvest_year": "VARCHAR(20)",
                "moisture": "FLOAT",
                "cupping_score": "FLOAT",
                "cupping_notes": "TEXT",
                "description": "TEXT",
                "image_url": "VARCHAR(255)",
                "additional_images": "TEXT",
                "featured": "BOOLEAN DEFAULT FALSE",
            },
        }
        inspector = inspect(db.engine)
        with db.engine.begin() as connection:
            for table, columns in legacy_columns.items():
                if not inspector.has_table(table):
                    continue
                existing = {column["name"] for column in inspector.get_columns(table)}
                for column, column_type in columns.items():
                    if column not in existing:
                        connection.execute(text(
                            f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
                        ))
        db.create_all()
        if not User.query.filter_by(email="admin@coffeelink.test").first():
            admin = User(name="Administrator", email="admin@coffeelink.test", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
        if Farmer.query.count() == 0:
            farmer = Farmer(name="Budi Santoso", village="Sukamakmur", region="Bandung, Jawa Barat",
                            phone="+62 812-0000-0001", email="budi@example.com", certification="Organik",
                            description="Third-generation coffee farmer producing specialty Arabica in the highlands of West Java.")
            db.session.add(farmer)
            db.session.commit()
            db.session.add(CoffeeProduct(
                name="Arabika Java Preanger",
                variety="Arabika",
                process="Washed",
                grade="Grade 1",
                stock_kg=1200,
                price_per_kg=8.5,
                origin="Bandung, Jawa Barat",
                farmer_id=farmer.id,
                harvest_year="2024",
                moisture=11.5,
                cupping_score=86.5,
                cupping_notes="Jasmine, citrus, brown sugar, clean finish",
                description="Premium washed Arabica from the historic Preanger region. Bright acidity with floral notes.",
                featured=True
            ))
            db.session.add(Buyer(company="Nordic Coffee Trading", contact_person="Anna Jensen",
                                 country="Denmark", email="buyer@example.com", phone="+45 0000 0000"))
            db.session.commit()

database_initialized = False


@app.before_request
def ensure_database_initialized():
    global database_initialized
    if request.endpoint == "database_health":
        return None
    if database_initialized:
        return None
    try:
        initialize_database()
        database_initialized = True
    except Exception as exc:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "database": str(exc),
        }), 503
    return None


@app.route("/__health/db")
def database_health():
    try:
        db.session.execute(text("SELECT 1"))
        db.session.commit()
        initialize_database()
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as exc:
        db.session.rollback()
        return jsonify({"status": "error", "database": str(exc)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)