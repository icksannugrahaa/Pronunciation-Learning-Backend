from flask import Flask
import pymongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from os.path import join, dirname
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = Flask(__name__)
cors = CORS(app)
jwt = JWTManager(app)

#env
app.config['API_BASE_URL'] = f"http://{os.environ.get('HOST')}:{os.environ.get('PORT')}"

#upload config
app.config["UPLOAD_FOLDER"] = os.path.dirname(app.instance_path)
app.config["ALLOWED_IMAGE_EXTENSIONS"] = set(['png', 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG', 'WAV', 'MP3', 'wav', 'mp3'])
app.config["ALLOWED_UPLOAD_BATCH_EXTENSIONS"] = set(['csv', 'xlsx', 'xls', 'xlt'])
print(os.environ.get('JWT_SECRET_KEY'))
#jwt config
app.config["JWT_SECRET_KEY"] = os.environ.get('JWT_SECRET_KEY')
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ERROR_MESSAGE_KEY"] = "message"

#cors config
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['PROPAGATE_EXCEPTIONS'] = True

try:
    mongo = pymongo.MongoClient(
        host=os.environ.get('DB_HOST'),
        port=int(os.environ.get('DB_PORT')) if os.environ.get('DB_PORT') else 27017,
        serverSelectionTimeoutMS=1000,
        username=os.environ.get('DB_USERNAME'),
        password=os.environ.get('DB_PASSWORD')
    )
    db = mongo.prolearn
    mongo.server_info()

    from .module import module as module_blueprint
    from .auth import auth as auth_blueprint
    from .file import file as file_blueprint
    from .account import account as account_blueprint
    from .progress import progress as progress_blueprint
    from .predict import predict as predict_blueprint
    

    app.register_blueprint(module_blueprint, url_prefix='/api/modules')
    app.register_blueprint(auth_blueprint, url_prefix='/api/auth')
    app.register_blueprint(file_blueprint, url_prefix='/api/file')
    app.register_blueprint(account_blueprint, url_prefix='/api/account')
    app.register_blueprint(progress_blueprint, url_prefix='/api/progress')
    app.register_blueprint(predict_blueprint, url_prefix='/api/predict')
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        tokenCollection = db.blockedToken
        cursor = list(tokenCollection.find({'jti': jti}))
        if len(cursor) == 0:
            return None
        else:
            for data in cursor:
                return data

except pymongo.errors.ConnectionFailure:
    print("Could not connect to MongoDB: %s")
