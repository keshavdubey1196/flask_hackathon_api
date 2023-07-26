from flask import Flask, jsonify, request
from models import db, init_db
from config import DATABASE_URI
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from models import User
import bcrypt
import ast


load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.secret_key = os.environ['SECRET_KEY']


# initializing flask-migrate with app and db
migrate = Migrate(app, db)


# to create all tables
init_db(app)


@app.route('/', methods=['GET'])
@app.route('/api/getinfo', methods=["GET"])
def getInfo():
    user = {"user":
            {
                "name": "required",
                "email": "required",
                "password": "required"
            }
            }
    submission = {"submission":
                  {
                      "file": "default",
                      "image": "if required",
                      "user_id": "required",
                      "hackathon_id": "required"
                  }
                  }
    required_data = [user, submission]
    return jsonify(required_data, 200)


@app.route('/api/getInfoDetailed/<string:name>/<int:id>', strict_slashes=False, methods=["GET"])
def getInfoDetailed(name, id):
    user = User.query.filter_by(name=name, id=id).first()

    if user is None:
        return jsonify({"error": "This admin does not exist"}), 404

    if not user.is_admin:
        return jsonify({"error": "You are not authorized"}), 401

    users = User.query.all()
    user_list = []
    for user in users:
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
        }
        user_list.append(user_data)

    if user_list:
        return jsonify(user_list), 200


@app.route('/api/users', methods=["GET"])
def getUsers():
    users = User.query.all()
    user_list = []

    # serializing each user and adding to list
    for user in users:
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        }
        user_list.append(user_data)

    return jsonify(user_list, 200)


@app.route('/api/users', methods=["POST"])
def addUser():
    data = request.get_json()

    # getting user data from JSON
    name = data["name"]
    email = data["email"]
    password = data["password"]
    is_admin_str = data.get('is_admin', "False")

    # to safely convert is_admin_str to bool
    try:
        is_admin = ast.literal_eval(is_admin_str)
    except (ValueError, SyntaxError):
        return jsonify({"error": "Invalid value for is_admin"})

    # validating required fields
    if not name or not email or not password:
        return jsonify(
            {
                "error": "Name, email and passoword are required fields"
            }), 400

    # to check if user exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            "error": "User exists with same email"
        }), 409

    # encrypt the password
    cipher_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(name=name, email=email,
                    password=cipher_password, is_admin=is_admin)

    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {
            "message": f"{new_user.name} with id = {new_user.id} added "
        }), 201


if __name__ == "__main__":
    app.run()
