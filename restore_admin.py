from app import app, db, InventoryItemUser
from werkzeug.security import generate_password_hash

with app.app_context():
    user = InventoryItemUser.query.filter_by(username='admin_user').first()
    if user is None:
        user = InventoryItemUser(username='admin_user', encrypt_password_hash=generate_password_hash('password1'))
        db.session.add(user)
        db.session.commit()
        print('Created admin_user with password password1')
    else:
        print('admin_user already exists')
    print('admin_count=', InventoryItemUser.query.filter_by(username='admin_user').count())
