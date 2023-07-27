from flask import Flask, jsonify, request
from models import db, init_db
from config import DATABASE_URI
from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from models import User, Hackathon
import bcrypt
import ast
from werkzeug.utils import secure_filename


load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.secret_key = os.environ['SECRET_KEY']


UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = set(['pdf', 'png', 'jpg', 'jpeg'])

# create folders if they don't exist in project
os.makedirs(os.path.join(UPLOAD_FOLDER, 'bg_imgs'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'hakthon_imgs'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'submission_imgs'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'files'), exist_ok=True)

# initializing flask-migrate with app and db
migrate = Migrate(app, db)


# to create all tables
init_db(app)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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


@app.route('/api/users/<int:user_id>', methods=["GET"])
def getUserById(user_id):
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        return jsonify({"error": "user does not exists"}, 404)

    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }
    return jsonify(user_data, 200)


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


@app.route('/api/addhackathon', methods=['POST'])
def add_hackathon():
    data = request.form
    title = data['title']
    description = data.get('description', 'OK')
    submission_type = data.get('submission_type', 'File')
    rewards = data.get('rewards', 500)
    start_datetime = data['start_datetime']
    end_datetime = data['end_datetime']
    creator_id = data['creator_id']
    bg_image = request.files['bg_image']
    hakthon_img = request.files['hakthon_img']

    # check if required data is provided
    if not title or not start_datetime or not end_datetime or not bg_image or not hakthon_img:
        data = {
            "title": "required",
            "start_datetime": "required",
            "end_datetime": "required",
            "bg_image": "required",
            "hakthon_img": "required",
            "creator_id": "required"
        }
        return jsonify(data, 400)

    if bg_image.filename or hakthon_img.filename == "":
        # print(bg_image.filename)
        # print(hakthon_img.filename)
        return jsonify({"error": "bg_image and hakthon_img must have filename"}), 400

    allowed = allowed_file(bg_image.filename) and allowed_file(
        hakthon_img.filename)

    if allowed:
        bg_image_filename = secure_filename(bg_image.filename)
        hakthon_img_filename = secure_filename(hakthon_img.filename)
        bg_image_path = os.path.join(
            app.config['UPLOAD_FOLDER'], 'bg_imgs', bg_image_filename)
        hakthon_img_path = os.path.join(
            app.config['UPLOAD_FOLDER'], 'hakthon_imgs', hakthon_img_filename)
        bg_image.save(bg_image_path)
        hakthon_img.save(hakthon_img_path)

        new_hackathon = Hackathon(
            title=title,
            description=description,
            bg_image=bg_image_filename,
            hakthon_img=hakthon_img_filename,
            submission_type=submission_type,
            rewards=rewards,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            creator_id=creator_id
        )
        db.session.add(new_hackathon)
        db.session.commit()
        return jsonify({"message": f"{new_hackathon.title} added!"}), 201
    else:
        return jsonify({"error": "Allowed file types are pdf, png, jpeg"}), 400


if __name__ == "__main__":
    app.run()
