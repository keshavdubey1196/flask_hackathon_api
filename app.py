from flask import Flask, jsonify
from models import db, init_db
from config import DATABASE_URI
from dotenv import load_dotenv
import os
from flask_migrate import Migrate


load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.secret_key = os.environ['SECRET_KEY']


# initializing flask-migrate with app and db
migrate = Migrate(app, db)


# to create all tables
init_db(app)


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


if __name__ == "__main__":
    app.run()
