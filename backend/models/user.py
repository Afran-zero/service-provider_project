# models/user.py
# Changes: Add unique=True to phone field
import mongoengine as me
from flask_login import UserMixin
import bcrypt
import datetime
import uuid

class User(me.Document, UserMixin):
    user_id = me.StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = me.StringField(required=True)
    email = me.EmailField(unique=True, required=True)
    phone = me.StringField(required=False)  # Changed: removed unique constraint to avoid index build errors
    password_hash = me.StringField(required=True)
    street_house = me.StringField(required=True)
    city = me.StringField(required=True)
    district = me.StringField(required=True)
    profile_pic_url = me.StringField(default=None)
    is_verified = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.datetime.utcnow)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def get_id(self):
        return str(self.user_id)

    meta = {
        'collection': 'users',
        'strict': False  # Allow documents with extra fields (ignore unknown fields)
    }