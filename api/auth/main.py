from flask import request
from api import db
from bson.objectid import ObjectId
from . import auth
import datetime
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from flask_cors import cross_origin
import bcrypt
from api.utils.mail_utils import Mail
import api.utils.data_utils as dataUtils

tokenCollection = db.blocked_tokens
accountDB = db.accounts


@auth.route('/me', methods=['POST'])
@jwt_required()
@cross_origin()
def me():
    results = {}
    response = 500
    if request.method == 'POST':
        if 'Authorization' in request.headers:
            email = get_jwt_identity()
            token = request.headers['Authorization']
            currentToken = token.split(' ')

            # Access DB
            cursor = list(accountDB.find({"email": email, "token": currentToken[1]}, {'name': 1, '_id': 0, 'email': 1, 'achievement': 1, 'status': 1, 'googleSignIn': 1, 'biodata': 1, 'phoneNumber': 1, 'gender': 1,
                                                            'exp': 1, 'level': 1, 'avatar': 1}))

            if len(cursor) == 0:
                results['message'] = "Your session is expired!"
                results['status'] = "error"
                response = 400
            else:
                for data in cursor:
                    results['message'] = "Data Found!"
                    results['status'] = "success"
                    results['data'] = data
                    response = 200
        else:
            results['message'] = "Your session is expired!"
            results['status'] = "error"
            response = 403
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405
    return results, response


@auth.route('/send-code', methods=['POST'])
@jwt_required()
@cross_origin()
def send_code():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        updatedAt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        currentAccount = request.form['email'] if 'email' in request.form and request.form['email'] != '' and request.form['email'] != 'null' else get_jwt_identity()
        code = dataUtils.code_generator()
        
        mail = Mail()
        mail.send(currentAccount, code, '', '', 'send-code')
        
        updateData = {
            'code': code,
            'updatedAt': updatedAt
        }
        
        accountDB.update_one(
            {'email': get_jwt_identity()},
            {'$set': updateData}
        )
        
        results['message'] = "Code verification has been send!"
        results['status'] = 'success'
        responses = 200
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
    
    return results, responses


@auth.route('/login', methods=['POST'])
@cross_origin()
def login():
    results = {}
    response = 500
    if request.method == 'POST':
        if 'email' in request.form and 'password' in request.form:
            email = request.form['email']
            password = str(request.form['password']).encode("utf-8")
            # Access DB
            finData = list(accountDB.find({"email": email}, {'name': 1, '_id': 1, 'email': 1, 'achievement': 1, 'status': 1, 'googleSignIn': 1, 'biodata': 1, 'phoneNumber': 1, 'gender': 1,
                                                             'exp': 1, 'level': 1, 'avatar': 1, 'password': 1}))

            if len(finData) == 0:
                results['message'] = "Email not found!"
                results['status'] = "error"
                response = 200
            else:
                if finData[0]['status'] == False:
                    results['message'] = "Please confirm your account first!"
                    results['status'] = "error"
                    response = 200
                else:
                    try:
                        if bcrypt.checkpw(password, finData[0]['password']):
                            finData[0]['_id'] = str(finData[0]["_id"])
                            access_token = create_access_token(
                                identity=finData[0]['email'], expires_delta=datetime.timedelta(hours=24))

                            accountDB.update_one(
                                {
                                    "_id": ObjectId(finData[0]["_id"])
                                },
                                {
                                    "$set": {
                                        "token": access_token
                                    }
                                }
                            )
                            finData[0].pop('password', None)
                            finData[0].pop('_id', None)
                            results['message'] = "Login Success!"
                            results['status'] = "success"
                            results['token'] = access_token
                            results['data'] = finData[0]
                            response = 200
                        else:
                            results['message'] = "Password doesn't match!"
                            results['status'] = "error"
                            response = 200
                    except Exception as e:
                        print(e)
                        results['message'] = "Internal Server Error."
                        results['status'] = "error"
                        response = 500

        else:
            results['message'] = "Please input a field!"
            results['status'] = "error"
            response = 200
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response


@auth.route('/expire', methods=['POST'])
@cross_origin()
def expire():
    results = {}
    response = 500
    if request.method == 'POST':
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            currentToken = token.split(' ')

            # Access DB
            cursor = list(accountDB.find(
                {"token": currentToken[1]}))

            if len(cursor) == 0:
                results['status'] = "error"
                results['message'] = "Your token is expired, Please login again!"
                response = 200
            else:
                try:
                    for data in cursor:
                        results['status'] = "success"
                        results['message'] = "Your session is expired!"
                        response = 200
                        accountDB.update_one(
                            {
                                "_id": ObjectId(data["_id"])
                            },
                            {
                                "$set": {
                                    "token": ""
                                }
                            }
                        )
                except:
                    results['message'] = "Internal Server Error."
                    results['status'] = "error"
                    response = 500
        else:
            results['message'] = "Your session is expired!"
            results['status'] = "error"
            response = 200
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response


@auth.route('/logout', methods=['POST'])
@jwt_required()
@cross_origin()
def logout():
    results = {}
    response = 500
    results['message'] = "Internal Server Error."
    results['status'] = "error"
    if request.method == 'POST':
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
            currentToken = token.split(' ')
            
            # Access DB
            cursor = list(accountDB.find(
                {"token": currentToken[1]}))

            if len(cursor) == 0:
                results['status'] = "error"
                results['message'] = "Your token is expired, please login again!"
                response = 200
            else:
                try:
                    for data in cursor:
                        results['status'] = "success"
                        results['message'] = "Logout Success!"
                        response = 200
                        jti = get_jwt()["jti"]
                        print(jti)
                        now = datetime.datetime.now()
                        tokenCollection.insert_one({
                            'jti': jti,
                            'created_at': now
                        })
                        accountDB.update_one(
                            {
                                "_id": ObjectId(data["_id"])
                            },
                            {
                                "$set": {
                                    "token": ""
                                }
                            }
                        )
                except:
                    results['message'] = "Internal Server Error."
                    results['status'] = "error"
                    response = 500
        else:
            results['message'] = "Your session is expired!"
            results['status'] = "error"
            response = 200
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response
