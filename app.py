import csv
import io
import json
import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, inspect, text
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
    Product_Type = db.Column(db.String(200), unique=True, nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItemModel(db.Model):
    __tablename__ = 'inventory_item_model'
    OID = db.Column(db.Integer, primary_key=True)
    Model_Number = db.Column(db.String(200), unique=True, nullable=False)
    add_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=False)
    add_datetime = db.Column(db.DateTime, nullable=False, default=func.now())
    update_user_oid = db.Column(db.Integer, db.ForeignKey('inventory_item_user.OID'), nullable=True)
    last_update_datetime = db.Column(db.DateTime, nullable=True)
    add_user = relationship('InventoryItemUser', foreign_keys=[add_user_oid], lazy='joined')
    update_user = relationship('InventoryItemUser', foreign_keys=[update_user_oid], lazy='joined')

class InventoryItemManufacturer(db.Model):
    __tablename__ = 'inventory_item_manufacturer'
    OID = db.Column(db.Integer, primary_key=True)
    Manufacturer_NAME = db.Column(db.String(200), unique=True, nullable=False)
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
    Item_Name = db.Column(db.String(250), unique=True, nullable=False)
    Note = db.Column(db.String(500), nullable=True)
    Alert_Level = db.Column(db.Integer, nullable=False, default=0)
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

def is_admin_user():
    return current_user.is_authenticated and current_user.username == 'admin_user'

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def get_latest_tracking():
    trackings = InventoryItemTracking.query.order_by(InventoryItemTracking.intentory_item_oid, InventoryItemTracking.last_update_datetime.desc()).all()
    latest = {}
    for tracking in trackings:
        oid = tracking.intentory_item_oid
        if oid not in latest:
            latest[oid] = tracking
    return latest

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
            latest_tracking = get_latest_tracking()
            alerts = []
            for item in InventoryItem.query.order_by(InventoryItem.Item_Name).all():
                tracking = latest_tracking.get(item.OID)
                count = tracking.item_count if tracking else 0
                if item.Alert_Level is not None and count < item.Alert_Level:
                    alerts.append(f'{item.Item_Name} is below alert level ({count} < {item.Alert_Level})')
            if alerts:
                flash('ALERT: ' + ' | '.join(alerts), 'warning')
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
    # filters from querystring
    type_oid = request.args.get('ITEM_TYPE_OID')
    model_oid = request.args.get('MODEL_OID')
    manufacturer_oid = request.args.get('Manufacturer_oid')

    item_types = InventoryItemType.query.order_by(InventoryItemType.Product_Type).all()
    item_models = InventoryItemModel.query.order_by(InventoryItemModel.Model_Number).all()
    manufacturers = InventoryItemManufacturer.query.order_by(InventoryItemManufacturer.Manufacturer_NAME).all()

    items_query = InventoryItem.query
    if type_oid:
        try:
            items_query = items_query.filter(InventoryItem.ITEM_TYPE_OID == int(type_oid))
        except ValueError:
            pass
    if model_oid:
        try:
            items_query = items_query.filter(InventoryItem.MODEL_OID == int(model_oid))
        except ValueError:
            pass
    if manufacturer_oid:
        try:
            items_query = items_query.filter(InventoryItem.Manufacturer_oid == int(manufacturer_oid))
        except ValueError:
            pass

    items = items_query.order_by(InventoryItem.Item_Name).all()
    trackings = InventoryItemTracking.query.order_by(InventoryItemTracking.intentory_item_oid, InventoryItemTracking.last_update_datetime.desc()).all()
    latest_tracking = {}
    for tracking in trackings:
        oid = tracking.intentory_item_oid
        if oid not in latest_tracking:
            latest_tracking[oid] = tracking

    tracked_items = []
    chart_data = []
    for item in items:
        tracking = latest_tracking.get(item.OID)
        count = tracking.item_count if tracking else 0
        last_update_user = tracking.update_user.username if tracking and tracking.update_user else 'N/A'
        last_update_datetime = tracking.last_update_datetime.strftime('%Y-%m-%d %H:%M') if tracking and tracking.last_update_datetime else 'N/A'

        tracked_items.append({
            'item': item,
            'count': count,
            'tracking_oid': tracking.OID if tracking else None
        })

        chart_data.append({
            'label': item.Item_Name,
            'count': count,
            'type': item.item_type.Product_Type if item.item_type else '',
            'model': item.model.Model_Number if item.model else '',
            'manufacturer': item.manufacturer.Manufacturer_NAME if item.manufacturer else '',
            'last_update_user': last_update_user,
            'item_name': item.Item_Name,
            'last_update_datetime': last_update_datetime
        })

    chart_json = json.dumps(chart_data)
    return render_template('dashboard.html', items=items, trackings=trackings, chart_data=chart_json,
                           tracked_items=tracked_items, item_types=item_types, item_models=item_models,
                           manufacturers=manufacturers, selected_type=type_oid, selected_model=model_oid,
                           selected_manufacturer=manufacturer_oid)

@app.route('/inventory')
@login_required
def inventory():
    item_types = InventoryItemType.query.order_by(InventoryItemType.Product_Type).all()
    item_models = InventoryItemModel.query.order_by(InventoryItemModel.Model_Number).all()
    manufacturers = InventoryItemManufacturer.query.order_by(InventoryItemManufacturer.Manufacturer_NAME).all()
    items = InventoryItem.query.order_by(InventoryItem.Item_Name).all()
    return render_template('inventory.html', item_types=item_types, item_models=item_models,
                           manufacturers=manufacturers, items=items)

@app.route('/inventory/export-csv')
@login_required
def export_inventory_csv():
    latest_tracking = get_latest_tracking()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Manufacturer', 'Item Name', 'Quantity', 'Notes', 'Product', 'Type', 'Model Number', 'Updated by'])

    items = InventoryItem.query.order_by(InventoryItem.Item_Name).all()
    for item in items:
        tracking = latest_tracking.get(item.OID)
        quantity = tracking.item_count if tracking else 0
        product = item.item_type.Product_Type if item.item_type else ''
        updated_by = item.update_user.username if item.update_user else (item.add_user.username if item.add_user else 'unknown')
        writer.writerow([
            item.manufacturer.Manufacturer_NAME if item.manufacturer else '',
            item.Item_Name,
            quantity,
            item.Note or '',
            product,
            '',
            item.model.Model_Number if item.model else '',
            updated_by
        ])

    csv_content = output.getvalue()
    output.close()
    return Response(csv_content,
                    mimetype='text/csv',
                    headers={
                        'Content-Disposition': 'attachment; filename=inventory_export.csv'
                    })

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
    product_type = request.form.get('Product_Type', '').strip()
    if not product_type:
        flash('Product type cannot be empty.', 'danger')
        return redirect(url_for('inventory'))

    existing = InventoryItemType.query.filter(func.lower(InventoryItemType.Product_Type) == product_type.lower()).first()
    if existing and (not oid or existing.OID != int(oid)):
        flash('Product type already exists.', 'danger')
        return redirect(url_for('inventory'))

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
    return redirect(url_for('inventory'))

@app.route('/model/save', methods=['POST'])
@login_required
def save_model():
    oid = request.form.get('OID')
    model_number = request.form.get('Model_Number', '').strip()
    if not model_number:
        flash('Model number cannot be empty.', 'danger')
        return redirect(url_for('inventory'))

    existing = InventoryItemModel.query.filter(func.lower(InventoryItemModel.Model_Number) == model_number.lower()).first()
    if existing and (not oid or existing.OID != int(oid)):
        flash('Model already exists.', 'danger')
        return redirect(url_for('inventory'))

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
    return redirect(url_for('inventory'))

@app.route('/manufacturer/save', methods=['POST'])
@login_required
def save_manufacturer():
    oid = request.form.get('OID')
    name = request.form.get('Manufacturer_NAME', '').strip()
    if not name:
        flash('Manufacturer name cannot be empty.', 'danger')
        return redirect(url_for('inventory'))

    existing = InventoryItemManufacturer.query.filter(func.lower(InventoryItemManufacturer.Manufacturer_NAME) == name.lower()).first()
    if existing and (not oid or existing.OID != int(oid)):
        flash('Manufacturer already exists.', 'danger')
        return redirect(url_for('inventory'))

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
    return redirect(url_for('inventory'))

@app.route('/type/delete', methods=['POST'])
@login_required
def delete_type():
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid product type selection.', 'danger')
        return redirect(url_for('inventory'))

    item_type = InventoryItemType.query.get(int(oid))
    if item_type is None:
        flash('Product type not found.', 'danger')
    elif InventoryItem.query.filter_by(ITEM_TYPE_OID=item_type.OID).first():
        flash('Cannot delete product type while it is used by inventory items.', 'danger')
    else:
        db.session.delete(item_type)
        db.session.commit()
        flash('Product type deleted.', 'success')
    return redirect(url_for('inventory'))

@app.route('/model/delete', methods=['POST'])
@login_required
def delete_model():
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid model selection.', 'danger')
        return redirect(url_for('inventory'))

    item_model = InventoryItemModel.query.get(int(oid))
    if item_model is None:
        flash('Model not found.', 'danger')
    elif InventoryItem.query.filter_by(MODEL_OID=item_model.OID).first():
        flash('Cannot delete model while it is used by inventory items.', 'danger')
    else:
        db.session.delete(item_model)
        db.session.commit()
        flash('Model deleted.', 'success')
    return redirect(url_for('inventory'))

@app.route('/manufacturer/delete', methods=['POST'])
@login_required
def delete_manufacturer():
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid manufacturer selection.', 'danger')
        return redirect(url_for('inventory'))

    manufacturer = InventoryItemManufacturer.query.get(int(oid))
    if manufacturer is None:
        flash('Manufacturer not found.', 'danger')
    elif InventoryItem.query.filter_by(Manufacturer_oid=manufacturer.OID).first():
        flash('Cannot delete manufacturer while it is used by inventory items.', 'danger')
    else:
        db.session.delete(manufacturer)
        db.session.commit()
        flash('Manufacturer deleted.', 'success')
    return redirect(url_for('inventory'))

@app.route('/item/delete', methods=['POST'])
@login_required
def delete_item():
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid inventory item selection.', 'danger')
        return redirect(url_for('inventory'))

    item = InventoryItem.query.get(int(oid))
    if item is None:
        flash('Inventory item not found.', 'danger')
    else:
        latest_tracking = InventoryItemTracking.query.filter_by(intentory_item_oid=item.OID).order_by(InventoryItemTracking.last_update_datetime.desc()).first()
        if latest_tracking and latest_tracking.item_count > 0:
            flash('Cannot delete inventory item while it has a tracked quantity above zero.', 'danger')
        else:
            db.session.delete(item)
            db.session.commit()
            flash('Inventory item deleted.', 'success')
    return redirect(url_for('inventory'))

@app.route('/item/save', methods=['POST'])
@login_required
def save_item():
    oid = request.form.get('OID')
    item_name = request.form.get('Item_Name', '').strip()
    item_type_oid = request.form.get('ITEM_TYPE_OID')
    model_oid = request.form.get('MODEL_OID')
    manufacturer_oid = request.form.get('Manufacturer_oid')
    note = request.form.get('Note', '').strip() or None
    alert_level = request.form.get('Alert_Level', '').strip()
    try:
        alert_level = int(alert_level) if alert_level else 0
        if alert_level < 0:
            alert_level = 0
    except ValueError:
        alert_level = 0

    if not item_name:
        flash('Item name cannot be empty.', 'danger')
        return redirect(url_for('inventory'))

    existing = InventoryItem.query.filter(func.lower(InventoryItem.Item_Name) == item_name.lower()).first()
    if existing and (not oid or existing.OID != int(oid)):
        flash('Item name already exists.', 'danger')
        return redirect(url_for('inventory'))

    if oid:
        item = InventoryItem.query.get(int(oid))
        item.Item_Name = item_name
        item.ITEM_TYPE_OID = int(item_type_oid)
        item.MODEL_OID = int(model_oid)
        item.Manufacturer_oid = int(manufacturer_oid)
        item.Note = note
        item.Alert_Level = alert_level
        item.update_user_oid = current_user.OID
        item.last_update_datetime = datetime.utcnow()
    else:
        item = InventoryItem(Item_Name=item_name, ITEM_TYPE_OID=int(item_type_oid), MODEL_OID=int(model_oid),
                             Manufacturer_oid=int(manufacturer_oid), Note=note, Alert_Level=alert_level,
                             add_user_oid=current_user.OID, add_date_time=datetime.utcnow(),
                             update_user_oid=current_user.OID, last_update_datetime=datetime.utcnow())
    db.session.add(item)
    db.session.commit()
    flash('Item saved.', 'success')
    return redirect(url_for('inventory'))

@app.route('/item/update-alert', methods=['POST'])
@login_required
def update_alert():
    oid = request.form.get('OID')
    alert_level = request.form.get('Alert_Level', '').strip()
    if not oid:
        flash('Invalid inventory item selection.', 'danger')
        return redirect(url_for('inventory'))

    try:
        alert_level_value = int(alert_level) if alert_level else 0
        if alert_level_value < 0:
            alert_level_value = 0
    except ValueError:
        flash('Invalid alert level value.', 'danger')
        return redirect(url_for('inventory'))

    item = InventoryItem.query.get(int(oid))
    if item is None:
        flash('Inventory item not found.', 'danger')
    else:
        item.Alert_Level = alert_level_value
        item.update_user_oid = current_user.OID
        item.last_update_datetime = datetime.utcnow()
        db.session.add(item)
        db.session.commit()
        flash('Alert level updated.', 'success')
    return redirect(url_for('inventory'))

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

@app.route('/tracking/adjust', methods=['POST'])
@login_required
def adjust_tracking():
    intentory_item_oid = request.form.get('intentory_item_oid')
    delta = request.form.get('delta')
    if not intentory_item_oid or delta is None:
        flash('Invalid inventory adjustment.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        delta = int(delta)
    except ValueError:
        flash('Invalid adjustment value.', 'danger')
        return redirect(url_for('dashboard'))

    item = InventoryItem.query.get(int(intentory_item_oid))
    if item is None:
        flash('Inventory item not found.', 'danger')
        return redirect(url_for('dashboard'))

    latest_tracking = InventoryItemTracking.query.filter_by(intentory_item_oid=item.OID).order_by(InventoryItemTracking.last_update_datetime.desc()).first()
    previous_count = latest_tracking.item_count if latest_tracking else 0
    new_count = max(0, previous_count + delta)

    tracking = InventoryItemTracking(intentory_item_oid=item.OID,
                                     item_count=new_count,
                                     update_user_oid=current_user.OID,
                                     last_update_datetime=datetime.utcnow())
    db.session.add(tracking)
    db.session.commit()

    action = 'updated'
    if delta > 0:
        action = 'increased'
    elif delta < 0:
        action = 'decreased'

    flash(f'Inventory count {action} to {tracking.item_count}.', 'success')
    if item.Alert_Level is not None and tracking.item_count < item.Alert_Level:
        flash(f'ALERT: {item.Item_Name} count {tracking.item_count} is below alert level {item.Alert_Level}.', 'warning')
    return redirect(url_for('dashboard'))

@app.route('/users')
@login_required
def users():
    if not is_admin_user():
        flash('User management is restricted to admin_user.', 'danger')
        return redirect(url_for('dashboard'))
    users = InventoryItemUser.query.order_by(InventoryItemUser.username).all()
    return render_template('users.html', users=users)

@app.route('/user/save', methods=['POST'])
@login_required
def save_user():
    if not is_admin_user():
        flash('Only admin_user may add or update users.', 'danger')
        return redirect(url_for('dashboard'))
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
        if user.username == 'admin_user' and username != 'admin_user':
            flash('admin_user username may not be changed.', 'danger')
            return redirect(url_for('users'))
        if user.username != 'admin_user':
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
    if not is_admin_user():
        flash('Only admin_user may delete users.', 'danger')
        return redirect(url_for('dashboard'))
    oid = request.form.get('OID')
    if not oid:
        flash('Invalid user selection.', 'danger')
        return redirect(url_for('users'))

    user = InventoryItemUser.query.get(int(oid))
    if user is None:
        flash('User not found.', 'danger')
    elif user.username == 'admin_user':
        flash('admin_user cannot be deleted.', 'danger')
    elif user.OID == current_user.OID:
        flash('You cannot delete your own account while logged in.', 'danger')
    else:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted.', 'success')
    return redirect(url_for('users'))

def ensure_database():
    db.create_all()

    inspector = inspect(db.engine)
    existing_columns = [col['name'] for col in inspector.get_columns('inventory_item')]
    with db.engine.connect() as connection:
        if 'Note' not in existing_columns:
            connection.execute(text('ALTER TABLE inventory_item ADD COLUMN Note VARCHAR(500)'))
        if 'Alert_Level' not in existing_columns:
            connection.execute(text('ALTER TABLE inventory_item ADD COLUMN Alert_Level INTEGER NOT NULL DEFAULT 0'))

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
    app.run(host='0.0.0.0', port=5000, debug=True)
