from flask import Flask
import pymongo
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager

basedir = os.getcwd()

app = Flask(__name__)
cors = CORS(app)
jwt = JWTManager(app)

#env
app.config['API_BASE_URL'] = f"http://{os.getenv('HOST')}:{os.getenv('PORT')}"

#upload config
app.config["UPLOAD_FOLDER"] = os.getenv('UPLOAD_FOLDER')
app.config["ALLOWED_IMAGE_EXTENSIONS"] = set(['png', 'jpg', 'jpeg', 'PNG', 'JPG', 'JPEG'])
app.config["ALLOWED_UPLOAD_BATCH_EXTENSIONS"] = set(['csv', 'xlsx', 'xls', 'xlt'])

#jwt config
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["SECRET_KEY"] = os.getenv('SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"
app.config["JWT_ERROR_MESSAGE_KEY"] = "message"

#cors config
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['PROPAGATE_EXCEPTIONS'] = True

try:
    mongo = pymongo.MongoClient(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        serverSelectionTimeoutMS=1000,
        username="sh",
        password="icksan0!"
    )
    db = mongo.prolearn
    mongo.server_info()

    from .module import module as module_blueprint
    

    app.register_blueprint(module_blueprint, url_prefix='/api/modules')
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        tokenCollection = db.blockedToken
        cursor = tokenCollection.find({'jti': jti})
        if cursor.count() == 0:
            return None
        else:
            for data in cursor:
                return data

except pymongo.errors.ConnectionFailure:
    print("Could not connect to MongoDB: %s")
