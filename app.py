from flask import Flask, jsonify, request, url_for, send_from_directory
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

app = Flask(__name__, static_url_path='/static', static_folder='/static')
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
    is_dot_in_filename = '.' in filename
    if_ext_in_allowed_extensions = filename.rsplit(
        '.', 1)[1].lower() in ALLOWED_EXTENSIONS

    return if_ext_in_allowed_extensions and is_dot_in_filename


def get_img_url(folder_name, filename):
    return url_for(
        'static', filename=f"uploads/{folder_name}/{filename}", _external=True)


@app.route('/uploads/bg_imgs/<filename>', methods=['GET'])
def get_bg_image(filename):
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], 'bg_imgs'), filename)


@app.route('/uploads/hakthon_imgs/<filename>', methods=['GET'])
def get_hakthon_image(filename):
    return send_from_directory(
        os.path.join(app.config['UPLOAD_FOLDER'], 'hakthon_imgs'), filename)


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
    if not (
            title and
            start_datetime and
            end_datetime and
            bg_image and
            hakthon_img):

        data = {
            "title": "required",
            "start_datetime": "required",
            "end_datetime": "required",
            "bg_image": "required",
            "hakthon_img": "required",
            "creator_id": "required"
        }
        return jsonify(data, 400)

    if (bg_image.filename == "") or (hakthon_img.filename == ""):
        # print(bg_image.filename)
        # print(hakthon_img.filename)
        return jsonify({"error": "images provided must have filename"}), 400

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
        return jsonify(
            {
                "message":
                f"{new_hackathon.title} added id = {new_hackathon.id}"
            }), 201
    else:
        return jsonify({"error": "Allowed file types are pdf, png, jpeg"}), 400


@app.route('/api/getuserhackathons/<int:user_id>', methods=['GET'])
def get_user_hackathons(user_id):
    user = User.query.filter_by(id=user_id).first()
    hackathons_list = []

    for hackathon in user.created_hackathons:
        data = {
            "id": hackathon.id,
            "title": hackathon.title,
            "description": hackathon.description,
            "bg_image": f"/uploads/bg_imgs/{hackathon.bg_image}",
            "hakthon_img": f"/uploads/hakthon_imgs/{hackathon.hakthon_img}",
            "submission_type": hackathon.submission_type,
            "rewards": hackathon.rewards,
            "created_at": hackathon.created_at,
            "start_datetime": hackathon.start_datetime,
            "end_datetime": hackathon.end_datetime,
            "creator_id": hackathon.creator_id
        }
        hackathons_list.append(data)

    return jsonify(hackathons_list), 200


@app.route('/api/participate', methods=['POST'])
def to_participate():
    data = request.get_json()

    user_id = data["user_id"]
    hackathon_id = data["hackathon_id"]

    if not (user_id and hackathon_id):
        return jsonify({"error": "provide both user_id and hackathon_id"}), 200

    user = User.query.filter_by(id=user_id).first()
    hackathon = Hackathon.query.filter_by(id=hackathon_id).first()

    if user is None or hackathon is None:
        return jsonify(
            {
                "error": "User or Hackathon or both not Found! Wrong Id(s)."
            }), 400

    # if hackathon is None:
    #     return jsonify({"error": "Hackathon Not Found! Wrong Id."}), 400

    # check if user is admin
    if user.is_admin:
        return jsonify({"error": "admins cannot participate"}), 400

    # is user already enrolled in hackathon
    if hackathon in user.participated_hackathons:
        return jsonify({
            "error": "User already in participating in this hackathon"
        }), 400

    # add user to list of hackathons
    user.participated_hackathons.append(hackathon)
    db.session.commit()

    return jsonify(
        {"message": f"{user.name} enrolled in {hackathon.title}"}), 200


if __name__ == '__main__':
    app.run()
