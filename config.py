from dotenv import load_dotenv
import os

load_dotenv()


db_user = os.environ["DB_USER"]
db_passwd = os.environ["DB_PASSWORD"]
db_host = os.environ["DB_HOST"]
db_port = os.environ["DB_PORT"]
db_name = os.environ["DB_NAME"]


DATABASE_URI = f"postgresql://{db_user}:{db_passwd}@{db_host}:{db_port}/{db_name}"
