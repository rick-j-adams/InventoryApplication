import unittest
from datetime import datetime

from werkzeug.security import generate_password_hash

from app import app, db, InventoryItem, InventoryItemManufacturer, InventoryItemModel, InventoryItemTracking, InventoryItemType, InventoryItemUser


class AuditSortTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

        self.app_context = app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        user = InventoryItemUser(username='admin_user', encrypt_password_hash=generate_password_hash('password1'))
        non_admin = InventoryItemUser(username='staff_user', encrypt_password_hash=generate_password_hash('password2'))
        db.session.add_all([user, non_admin])
        db.session.commit()

        type_a = InventoryItemType(Product_Type='Type A', add_user_oid=user.OID, add_datetime=datetime.utcnow(), update_user_oid=user.OID, last_update_datetime=None)
        model_a = InventoryItemModel(Model_Number='Model A', add_user_oid=user.OID, add_datetime=datetime.utcnow(), update_user_oid=user.OID, last_update_datetime=None)
        manufacturer_a = InventoryItemManufacturer(Manufacturer_NAME='Manufacturer A', add_user_oid=user.OID, add_date_time=datetime.utcnow(), update_user_oid=user.OID, last_update_datetime=None)
        db.session.add_all([type_a, model_a, manufacturer_a])
        db.session.commit()

        item_b = InventoryItem(
            ITEM_TYPE_OID=type_a.OID,
            MODEL_OID=model_a.OID,
            Manufacturer_oid=manufacturer_a.OID,
            Item_Name='Beta',
            Note='Second',
            Alert_Level=1,
            add_user_oid=user.OID,
            add_date_time=datetime.utcnow(),
            update_user_oid=user.OID,
            last_update_datetime=datetime(2024, 1, 10, 0, 0, 0),
        )
        item_a = InventoryItem(
            ITEM_TYPE_OID=type_a.OID,
            MODEL_OID=model_a.OID,
            Manufacturer_oid=manufacturer_a.OID,
            Item_Name='Alpha',
            Note='First',
            Alert_Level=1,
            add_user_oid=user.OID,
            add_date_time=datetime.utcnow(),
            update_user_oid=user.OID,
            last_update_datetime=datetime(2024, 1, 1, 0, 0, 0),
        )
        db.session.add_all([item_b, item_a])
        db.session.commit()

        tracking_b = InventoryItemTracking(intentory_item_oid=item_b.OID, item_count=2, update_user_oid=user.OID, last_update_datetime=datetime(2024, 1, 10, 0, 0, 0))
        tracking_a = InventoryItemTracking(intentory_item_oid=item_a.OID, item_count=5, update_user_oid=user.OID, last_update_datetime=datetime(2024, 1, 1, 0, 0, 0))
        db.session.add_all([tracking_b, tracking_a])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_audit_page_can_sort_by_item_or_last_modified(self):
        client = app.test_client()
        login_response = client.post('/login', data={'username': 'admin_user', 'password': 'password1'}, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)

        item_sorted = client.get('/audit?sort_by=item').get_data(as_text=True)
        self.assertIn('sort_by', item_sorted)
        self.assertLess(item_sorted.index('Alpha'), item_sorted.index('Beta'))

        modified_sorted = client.get('/audit?sort_by=last_modified').get_data(as_text=True)
        self.assertIn('sort_by', modified_sorted)
        self.assertLess(modified_sorted.index('Beta'), modified_sorted.index('Alpha'))

    def test_non_admin_cannot_add_or_delete_inventory_items(self):
        client = app.test_client()
        login_response = client.post('/login', data={'username': 'staff_user', 'password': 'password2'}, follow_redirects=True)
        self.assertEqual(login_response.status_code, 200)

        item_count_before = InventoryItem.query.count()
        add_response = client.post('/item/save', data={
            'Item_Name': 'Restricted Item',
            'ITEM_TYPE_OID': '1',
            'MODEL_OID': '1',
            'Manufacturer_oid': '1',
            'Note': 'should not be added',
            'Alert_Level': '2',
        }, follow_redirects=False)
        self.assertEqual(add_response.status_code, 302)
        self.assertEqual(InventoryItem.query.count(), item_count_before)

        item = InventoryItem.query.filter_by(Item_Name='Alpha').first()
        delete_response = client.post('/item/delete', data={'OID': str(item.OID)}, follow_redirects=False)
        self.assertEqual(delete_response.status_code, 302)
        self.assertIsNotNone(InventoryItem.query.get(item.OID))

    def test_default_admin_user_is_restored_when_missing(self):
        admin = InventoryItemUser.query.filter_by(username='admin_user').first()
        if admin:
            db.session.delete(admin)
            db.session.commit()

        with app.app_context():
            from app import ensure_default_admin_user
            self.assertTrue(ensure_default_admin_user())

        restored = InventoryItemUser.query.filter_by(username='admin_user').first()
        self.assertIsNotNone(restored)


if __name__ == '__main__':
    unittest.main()
