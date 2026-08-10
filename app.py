import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.orm import relationship

basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_path = os.path.join(basedir, 'inventory.db').replace('\\', '/')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change_this_secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{sqlite_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class InventoryItemUser(UserMixin, db.Model):
    __tablename__ = 'inventory_item_user'
    OID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    encrypt_password_hash = db.Column(db.String(255), nullable=False)
    def get_id(self):
        return str(self.OID)

class InventoryItemType(db.Model):
    __tablename__ = 'inventory_item_type'
    OID = db.Column(db.Integer, primary_key=True)
    Product_Type = db.Column(db.String(200), nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItemModel(db.Model):
    __tablename__ = 'inventory_item_model'
    OID = db.Column(db.Integer, primary_key=True)
    Model_Number = db.Column(db.String(200), nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItemManufacturer(db.Model):
    __tablename__ = 'inventory_item_manufacturer'
    OID = db.Column(db.Integer, primary_key=True)
    Manufacturer_NAME = db.Column(db.String(200), nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_date_time = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItem(db.Model):
    __tablename__ = 'inventory_item'
    OID = db.Column(db.Integer, primary_key=True)
    ITEM_TYPE_OID = db.Column(db.Integer, db.ForeignKey('inventory_item_type.OID'), nullable=False)
    MODEL_OID = db.Column(db.Integer, db.ForeignKey('inventory_item_model.OID'), nullable=False)
    Manufacturer_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_manufacturer.OID'), nullable=False)
    Item_Name = db.Column(db.String(250), nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_date_time = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    item_type = relationship('InventoryItemType', foreign_keys=[ITEM_TYPE_OID], lazy='joined')
    model = relationship('InventoryItemModel', foreign_keys=[MODEL_OID], lazy='joined')
    manufacturer = relationship('InventoryItemManufacturer', foreign_keys=[Manufacturer_oid], lazy='joined')
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItemTracking(db.Model):
    __tablename__ = 'inventory_item_tracking'
    OID = db.Column(db.Integer, primary_key=True)
    intentory_item_oid = db.Column(db.Integer, db.ForeignKey('inventory_item.OID'), nullable=False)
    item_count = db.Column(db.Integer, nullable=False, default=0)
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    last_update_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    item = relationship('InventoryItem', foreign_keys=[intentory_item_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

@login_manager.user_loader
def load_user(user_id):
    return InventoryItemUser.query.get(int(user_id))

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = InventoryItemUser.query.filter_by(username=username).first()
        if user and check_password_hash(user.encrypt_password_hash, password):
            login_user(user)
            flash('Welcome back, {}'.format(user.username), 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

def create_or_update_entity(model, form_data, obj=None):
    if obj is None:
        obj = model()
        obj.add_user_oid = current_user.OID
        obj.add_datetime = datetime.utcnow()
    obj.update_user_oid = current_user.OID
    obj.last_update_datetime = datetime.utcnow()
    for key, value in form_data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    return obj

@app.route('/dashboard')
@login_required
def dashboard():
    item_types = InventoryItemType.query.order_by(InventoryItemType.Product_Type).all()
    item_models = InventoryItemModel.query.order_by(InventoryItemModel.Model_Number).all()
    manufacturers = InventoryItemManufacturer.query.order_by(InventoryItemManufacturer.Manufacturer_NAME).all()
    items = InventoryItem.query.order_by(InventoryItem.Item_Name).all()
    trackings = InventoryItemTracking.query.order_by(InventoryItemTracking.OID.desc()).all()
    return render_template('dashboard.html', item_types=item_types, item_models=item_models,
                           manufacturers=manufacturers, items=items, trackings=trackings)

@app.route('/audit')
@login_required
def audit_log():
    item_types = InventoryItemType.query.order_by(InventoryItemType.add_datetime.desc()).all()
    item_models = InventoryItemModel.query.order_by(InventoryItemModel.add_datetime.desc()).all()
    manufacturers = InventoryItemManufacturer.query.order_by(InventoryItemManufacturer.add_date_time.desc()).all()
    items = InventoryItem.query.order_by(InventoryItem.add_date_time.desc()).all()
    trackings = InventoryItemTracking.query.order_by(InventoryItemTracking.last_update_datetime.desc()).all()
    return render_template('audit.html', item_types=item_types, item_models=item_models,
                           manufacturers=manufacturers, items=items, trackings=trackings)

@app.route('/type/save', methods=['POST'])
@login_required
def save_type():
    oid = request.form.get('OID')
    product_type = request.form.get('Product_Type')
    if oid:
        item_type = InventoryItemType.query.get(int(oid))
        item_type.Product_Type = product_type
    else:
        item_type = InventoryItemType(Product_Type=product_type, add_user_oid=current_user.OID,
                                      add_datetime=datetime.utcnow(), update_user_oid=current_user.OID,
                                      last_update_datetime=datetime.utcnow())
    db.session.add(item_type)
    db.session.commit()
    flash('Product type saved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/model/save', methods=['POST'])
@login_required
def save_model():
    oid = request.form.get('OID')
    model_number = request.form.get('Model_Number')
    if oid:
        item_model = InventoryItemModel.query.get(int(oid))
        item_model.Model_Number = model_number
    else:
        item_model = InventoryItemModel(Model_Number=model_number, add_user_oid=current_user.OID,
                                        add_datetime=datetime.utcnow(), update_user_oid=current_user.OID,
                                        last_update_datetime=datetime.utcnow())
    db.session.add(item_model)
    db.session.commit()
    flash('Model saved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/manufacturer/save', methods=['POST'])
@login_required
def save_manufacturer():
    oid = request.form.get('OID')
    name = request.form.get('Manufacturer_NAME')
    if oid:
        manufacturer = InventoryItemManufacturer.query.get(int(oid))
        manufacturer.Manufacturer_NAME = name
    else:
        manufacturer = InventoryItemManufacturer(Manufacturer_NAME=name, add_user_oid=current_user.OID,
                                                 add_date_time=datetime.utcnow(), update_user_oid=current_user.OID,
                                                 last_update_datetime=datetime.utcnow())
    db.session.add(manufacturer)
    db.session.commit()
    flash('Manufacturer saved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/item/save', methods=['POST'])
@login_required
def save_item():
    oid = request.form.get('OID')
    item_name = request.form.get('Item_Name')
    item_type_oid = request.form.get('ITEM_TYPE_OID')
    model_oid = request.form.get('MODEL_OID')
    manufacturer_oid = request.form.get('Manufacturer_oid')
    if oid:
        item = InventoryItem.query.get(int(oid))
        item.Item_Name = item_name
        item.ITEM_TYPE_OID = int(item_type_oid)
        item.MODEL_OID = int(model_oid)
        item.Manufacturer_oid = int(manufacturer_oid)
        item.update_user_oid = current_user.OID
        item.last_update_datetime = datetime.utcnow()
    else:
        item = InventoryItem(Item_Name=item_name, ITEM_TYPE_OID=int(item_type_oid), MODEL_OID=int(model_oid),
                             Manufacturer_oid=int(manufacturer_oid), add_user_oid=current_user.OID,
                             add_date_time=datetime.utcnow(), update_user_oid=current_user.OID,
                             last_update_datetime=datetime.utcnow())
    db.session.add(item)
    db.session.commit()
    flash('Item saved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/tracking/save', methods=['POST'])
@login_required
def save_tracking():
    oid = request.form.get('OID')
    intentory_item_oid = request.form.get('intentory_item_oid')
    item_count = request.form.get('item_count')
    if oid:
        tracking = InventoryItemTracking.query.get(int(oid))
        tracking.item_count = int(item_count)
        tracking.update_user_oid = current_user.OID
        tracking.last_update_datetime = datetime.utcnow()
    else:
        tracking = InventoryItemTracking(intentory_item_oid=int(intentory_item_oid), item_count=int(item_count),
                                         update_user_oid=current_user.OID, last_update_datetime=datetime.utcnow())
    db.session.add(tracking)
    db.session.commit()
    flash('Tracking entry saved.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/users')
@login_required
def users():
    users = InventoryItemUser.query.order_by(InventoryItemUser.username).all()
    return render_template('users.html', users=users)

@app.route('/user/save', methods=['POST'])
@login_required
def save_user():
    oid = request.form.get('OID')
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username:
        flash('Username cannot be empty.', 'danger')
        return redirect(url_for('users'))

    existing = InventoryItemUser.query.filter(InventoryItemUser.username == username).first()
    if existing and (not oid or existing.OID != int(oid)):
        flash('Username already exists.', 'danger')
        return redirect(url_for('users'))

    if oid:
        user = InventoryItemUser.query.get(int(oid))
        if user is None:
            flash('User not found.', 'danger')
            return redirect(url_for('users'))
        user.username = username
        if password:
            user.encrypt_password_hash = generate_password_hash(password)
        flash('User updated.', 'success')
    else:
        if not password:
            flash('Password is required for new users.', 'danger')
            return redirect(url_for('users'))
        user = InventoryItemUser(username=username, encrypt_password_hash=generate_password_hash(password))
        db.session.add(user)
        flash('New user added.', 'success')

    db.session.commit()
    return redirect(url_for('users'))

@app.route('/user/delete', methods=['POST'])
@login_required
def delete_user():
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid user selection.', 'danger')
        return redirect(url_for('users'))

    user = InventoryItemUser.query.get(int(oid))
    if user is None:
        flash('User not found.', 'danger')
    elif user.OID == current_user.OID:
        flash('You cannot delete your own account while logged in.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')
    return redirect(url_for('users'))

def ensure_database():
    db.create_all()
    if not InventoryItemUser.query.filter_by(username='admin_user').first():
        password_hash = generate_password_hash('password1')
        admin = InventoryItemUser(username='admin_user', encrypt_password_hash=password_hash)
        db.session.add(admin)
        db.session.commit()
        print('Created admin_user with password password1')
    else:
        print('admin_user already exists')

@app.cli.command('init-db')
def init_db():
    ensure_database()

if __name__ == '__main__':
    with app.app_context():
        ensure_database()
    app.run(debug=True)
