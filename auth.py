import os
import datetime
import functools
import json

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from database import SessionLocal
from models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")

JWT_SECRET = os.getenv("JWT_SECRET", "please_change_me")
JWT_ALGO = "HS256"
JWT_EXP_MINUTES = int(os.getenv("JWT_EXP_MINUTES", "480")) 

def create_token(user_id, role):
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=JWT_EXP_MINUTES),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except Exception as e:
        return None

def token_required(f):
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth:
            return jsonify({"error": "Missing Authorization header"}), 401
        parts = auth.split()
        if parts[0].lower() != "bearer" or len(parts) != 2:
            return jsonify({"error": "Invalid auth header"}), 401
        token = parts[1]
        data = decode_token(token)
        if not data:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.user = {"id": data.get("sub"), "role": data.get("role")}
        return f(*args, **kwargs)
    return wrap

def role_required(allowed_roles):
    if isinstance(allowed_roles, str):
        roles = [allowed_roles]
    else:
        roles = list(allowed_roles)
    def deco(f):
        @functools.wraps(f)
        @token_required
        def wrap(*args, **kwargs):
            user_role = getattr(request, "user", {}).get("role")
            if user_role not in roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return f(*args, **kwargs)
        return wrap
    return deco

# Register endpoint

@bp.route("/register", methods=["POST"])
def register():
    db = SessionLocal()
    data = request.json or {}
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "CANDIDATE").upper()

    if not username or not email or not password:
        return jsonify({"error": "username,email,password required"}), 400

    if db.query(User).filter(User.username == username).first():
        return jsonify({"error": "username already exists"}), 400
    if db.query(User).filter(User.email == email).first():
        return jsonify({"error": "email already exists"}), 400

    password_hash = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=password_hash, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.role)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "token": token
    })



@bp.route("/login", methods=["POST"])
def login():
    db = SessionLocal()
    data = request.json or {}
    login_id = data.get("login")  # can be username or email
    password = data.get("password")
    if not login_id or not password:
        return jsonify({"error": "login and password required"}), 400

    user = db.query(User).filter((User.username == login_id) | (User.email == login_id)).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_token(user.id, user.role)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "token": token
    })



@bp.route("/me", methods=["GET"])
@token_required
def me():
    db = SessionLocal()
    uid = request.user.get("id")
    u = db.query(User).filter(User.id == uid).first()
    if not u:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "role": u.role
    })
