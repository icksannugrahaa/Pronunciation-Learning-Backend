from hashlib import new
import os
from flask import request
from api import app, db
from bson.objectid import ObjectId
import re
from . import account
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_cors import cross_origin
from datetime import datetime
import datetime as date_time
import pymongo
import bcrypt
import io
import csv
import json
from .schema import registerAccountSchema, resetPasswordSchema, changePasswordSchema, updateSchema, updateEmailSchema
import api.utils.data_utils as dataUtils
from api.utils.mail_utils import Mail
from urllib.parse import urlparse

accountCollection = db.accounts
cardCollection = db.cards
apiModule = 'account'

def validateForm(request, event):
    reqData = {}
    reqForm = request.form.to_dict(flat=False)
    for data in reqForm:
        reqData[data] = reqForm[data][0]
    if event == 'change_password':
        validation_result = changePasswordSchema.validate(reqData)
    elif event == 'reset_password':
        validation_result = resetPasswordSchema.validate(reqData)
    elif event == 'update_account':
        validation_result = updateSchema.validate(reqData)
    elif event == 'register_account':
        validation_result = registerAccountSchema.validate(reqData)
    elif event == 'update_email':
        validation_result = updateEmailSchema.validate(reqData)

    return validation_result


def process_filter(request):
    output = []
    outputs = []
    query = {}
    filter = {}
    sortBy = request.form['sortBy'] if 'sortBy' in request.form and request.form['sortBy'] != '' else '_id'
    orderBy = pymongo.DESCENDING if 'orderBy' in request.form and request.form[
        'orderBy'] == 'desc' and request.form['orderBy'] != '' else pymongo.ASCENDING
    page = int(request.form['page']
               ) if 'page' in request.form and request.form['page'] != '' else 1
    limit = int(request.form['limit']
                ) if 'limit' in request.form and request.form['limit'] != '0' and request.form['limit'] != '' else 10
    offset = (page * limit) - limit
    # default data
    

    if 'search' in request.form and request.form['search'] != '':
        query["name"] = re.compile(request.form['search'], re.IGNORECASE)

    findAccount = accountCollection.find(query, filter).sort(
        sortBy, orderBy).skip(offset).limit(limit)
    allData = accountCollection.find(query, filter).sort(
        sortBy, orderBy)
    for data in findAccount:
        output.append(data)
    for alldata in allData:
        outputs.append(alldata)
    return [output, dataUtils.get_paginated_list(outputs, offset, limit, page)]


@account.route('/register', methods=['POST'])
@cross_origin()
def register():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        validation_result = validateForm(request, 'register_account')
        if validation_result.get('success', False) is True:
            checkEmail = list(accountCollection.find({'email': request.form['email']}))
            createdAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if(len(checkEmail) > 0):
                checkStatus = list(accountCollection.find({'email': request.form['email'], 'status': False, 'code': checkEmail[0]['code']}))
                if(len(checkStatus) > 0):
                    code = dataUtils.code_generator()
                    insertData = {
                        'code': code,
                        'createdAt': createdAt
                    }
                    host = request.host_url
                    codes = str(code+"-"+createdAt).encode("utf-8")
                    encryptCodes = bcrypt.hashpw(codes, bcrypt.gensalt())
                    mail = Mail()
                    mail.send(request.form['email'], code, encryptCodes.decode("utf-8"), host, 'registration')
                    accountCollection.update_one(
                        {'email': request.form['email'], 'status': False, 'code': checkEmail[0]['code']},
                        {'$set': insertData}
                    )
                    results['message'] = "Account has been created, please confirm from your email!"
                    results['status'] = 'success'
                    responses = 201
                else:
                    results['message'] = "Email have been used!"
                    results['status'] = 'error'
                    responses = 200
            else: 
                try:
                    psw = str(request.form['password']).encode("utf-8")
                    code = dataUtils.code_generator()
                    insertData = {
                        'email': request.form['email'],
                        'password': bcrypt.hashpw(psw, bcrypt.gensalt()),
                        'achievement': [],
                        'googleSignIn': False,
                        'name': request.form['name'],
                        'exp': 0,
                        'level': 1,
                        'avatar': '/api/file?show=guest.png&path=/images',
                        'gender': None,
                        'biodata': None,
                        'phoneNumber': None,
                        'status': False,
                        'token': None,
                        'code': code,
                        'createdAt': createdAt
                    }
                    
                    host = request.host_url
                    codes = str(code+"-"+createdAt).encode("utf-8")
                    encryptCodes = bcrypt.hashpw(codes, bcrypt.gensalt())
                    mail = Mail()
                    mail.send(request.form['email'], code, encryptCodes.decode("utf-8"), host, 'registration')
                    
                    accountCollection.insert_one(insertData)
                    results['message'] = "Account has been created, please confirm from your email!"
                    results['status'] = 'success'
                    responses = 201
                except Exception as e:
                    print(e)
                    results['message'] = "Internal Server Error!"
                    results['status'] = 'error'
                    responses = 500
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
        
    return results, responses

@account.route('/verify', methods=['GET'])
@cross_origin()
def verify():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'GET':
        if 'code' in request.args and request.args.get('code') != '' and request.args.get('code') != 'null' and 'key' in request.args and request.args.get('key') != '' and request.args.get('key') != 'null':
            findCode = list(accountCollection.find({'code': request.args['code']}))
            if(len(findCode) <= 0):
                results['message'] = "Verification failed!, please try to register again!"
                results['status'] = 'error'
                responses = 200
            else:
                code = str(findCode[0]['code']+"-"+findCode[0]['createdAt']).encode("utf-8")
                key = str(request.args.get('key')).encode("utf-8")
                if bcrypt.checkpw(code, key):
                    try:
                        updatedAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                        mail = Mail()
                        mail.send(findCode[0]['email'], '', '', '', 'verify')
                        
                        updateData = {
                            'status': True,
                            'code': None,
                            'updatedAt': updatedAt
                        }
                        
                        accountCollection.update_one(
                            {'email': findCode[0]['email']},
                            {'$set': updateData}
                        )

                        results['message'] = "Account has been verified!"
                        results['status'] = 'success'
                        responses = 200
                    except Exception as e:
                        print(e)
                        results['message'] = "Internal Server Error!"
                        results['status'] = 'error'
                        responses = 500
                else:
                    results['message'] = "Verification failed!, please try to register again!"
                    results['status'] = 'error'
                    responses = 400
        else:
            results['message'] = "Verification failed!, please try to register again!"
            results['status'] = 'error'
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
        
    return results, responses

@account.route('/reset-password', methods=['POST'])
@cross_origin()
def reset_password():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        validation_result = validateForm(request, 'reset_password')
        if validation_result.get('success', False) is True:
            newPassword = dataUtils.code_generator(8)
            newPasswordEncoded = str(newPassword).encode('utf-8')
            
            mail = Mail()
            mail.send(request.form['email'], newPassword, '', '', 'reset-password')
            updatedAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            updateData = {
                'password': bcrypt.hashpw(newPasswordEncoded, bcrypt.gensalt()),
                'updatedAt': updatedAt
            }
            accountCollection.update_one(
                {'email': request.form['email']},
                {'$set': updateData}
            )
            results['message'] = "Password has been reset, check your email!"
            results['status'] = 'success'
            responses = 200
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
    
    return results, responses

@account.route('/change-password', methods=['POST'])
@jwt_required()
@cross_origin()
def change_password():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        validation_result = validateForm(request, 'change_password')
        if validation_result.get('success', False) is True:
            currentPassword = str(request.form['currentPassword']).encode("utf-8")
            newPassword = str(request.form['newPassword']).encode("utf-8")
            if bcrypt.checkpw(currentPassword,account[0]['password']):
                if request.form['newPassword'] == request.form['cPassword']:
                    updatedAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    updateData = {
                        'password': bcrypt.hashpw(newPassword, bcrypt.gensalt()),
                        'updatedAt': updatedAt
                    }
                    accountCollection.update_one(
                        {'email': account[0]['email']},
                        {'$set': updateData}
                    )
                    results['message'] = "Password has been updated!"
                    results['status'] = 'success'
                    responses = 200
                else:
                    results['message'] = "Password confirmation is incorrect!"
                    results['status'] = 'error'
                    responses = 200
            else:
                results['message'] = "Current password is incorrect!"
                results['status'] = 'error'
                responses = 200
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
    
    return results, responses


@account.route('/update-account', methods=['POST'])
@jwt_required()
@cross_origin()
def update_account():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        validation_result = validateForm(request, 'update_account')
        if validation_result.get('success', False) is True:
            updateData = {}
            updateData['updatedAt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for key in request.form.keys():
                for value in request.form.getlist(key):
                    if key == 'status' or key == 'googleSignIn':
                        updateData[key] = True if value == "true" else False
                    else:
                        updateData[key] = value
                
            accountCollection.update_one(
                {"email": currentAccount},
                {"$set": updateData}
            )
            results['message'] = "Account has been updated!"
            results['status'] = 'success'
            responses = 200
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
    
    return results, responses


@account.route('/update-email', methods=['POST'])
@jwt_required()
@cross_origin()
def update_email():
    results = {}
    responses = 500
    results['message'] = "Internal Server Error!"
    results['status'] = 'error'
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        validation_result = validateForm(request, 'update_email')
        if validation_result.get('success', False) is True:
            currentPassword = str(request.form['currentPassword']).encode("utf-8")
            if bcrypt.checkpw(currentPassword,account[0]['password']):
                if request.form['code'] == account[0]['code']:
                    updatedAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    access_token = create_access_token(identity=request.form['email'], expires_delta=date_time.timedelta(minutes=30))
                    updateData = {
                        'email': request.form['email'],
                        'updatedAt': updatedAt,
                        'code': None,
                        'token': access_token
                    }
                    
                    accountCollection.update_one(
                        {"email": currentAccount},
                        {"$set": updateData}
                    )
                    accountNew = list(accountCollection.find({'email': request.form['email']}))[0]
                    accountNew['_id'] = str(accountNew['_id'])
                    results['message'] = "Email has been updated!"
                    results['data'] = accountNew
                    results['token'] = access_token
                    results['status'] = 'success'
                    responses = 200
                else:
                    results['message'] = "Verification code is incorrect!"
                    results['status'] = 'error'
                    responses = 200
            else:
                results['message'] = "Password is incorrect!"
                results['status'] = 'error'
                responses = 200
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            responses = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405
    
    return results, responses