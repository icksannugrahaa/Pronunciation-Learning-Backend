from flask import request
from api import db
from . import module
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import re
import api.utils.data_utils as dataUtils
from bson.objectid import ObjectId
from .schema import storeReview
from datetime import datetime

# initial db
moduleCollection = db.modules
scoreboardCollection = db.scoreboards
accountCollection = db.accounts

def validateForm(request, event):
    reqData = {}
    reqForm = request.form.to_dict(flat=False)
    for data in reqForm:
        reqData[data] = reqForm[data][0]
    if event == 'store_review':
        validation_result = storeReview.validate(reqData)
    
    return validation_result

def process_data_scoreboard(request):
    output = []
    outputs = []
    query = {}
    custom_order = {'sort_by': 'score', 'order_by': 'desc', 'limit': 100}
    pageData = dataUtils.get_pagination_data(request, custom_order)
    
    if 'search' in request.form and request.form['search'] != '' and request.form['search'] != 'null':
        query['lesson'] = re.compile(
            request.form['search'], re.IGNORECASE)
    if 'find' in request.form and request.form['find'] != '' and request.form['find'] != 'null':
        query['_id'] = ObjectId(request.form['find'])
    print(query)
    findData = scoreboardCollection.find(query).sort(pageData['sortBy'], pageData['orderBy']).skip(pageData['offset']).limit(pageData['limit'])
    findAllData = scoreboardCollection.find(query).sort(pageData['sortBy'], pageData['orderBy'])
    
    for data in findData:
        data['_id'] = str(data['_id'])
        output.append(data)
    for alldata in findAllData:
        alldata['_id'] = str(alldata['_id'])
        outputs.append(alldata)

    if 'limit' in request.form:
        return {'data': output, 'paginated': dataUtils.get_paginated_list(outputs, pageData['offset'], pageData['limit'], pageData['page'])}
    else:
        return {'data': output, 'paginated': dataUtils.get_paginated_list(outputs, pageData['offset'], pageData['limit'], pageData['page'])}

def process_data(request):
    output = []
    outputs = []
    query = {}
    custom_order = {'sort_by': 'order'}
    pageData = dataUtils.get_pagination_data(request, custom_order)
    
    if 'search' in request.form and request.form['search'] != '' and request.form['search'] != 'null':
        query['name'] = re.compile(
            request.form['search'], re.IGNORECASE)
    if 'find' in request.form and request.form['find'] != '' and request.form['find'] != 'null':
        query['_id'] = ObjectId(request.form['find'])
    print(query)
    findData = moduleCollection.find(query).sort(pageData['sortBy'], pageData['orderBy']).skip(pageData['offset']).limit(pageData['limit'])
    findAllData = moduleCollection.find(query).sort(pageData['sortBy'], pageData['orderBy'])
    
    for data in findData:
        data['_id'] = str(data['_id'])
        output.append(data)
    for alldata in findAllData:
        alldata['_id'] = str(alldata['_id'])
        outputs.append(alldata)

    if 'limit' in request.form:
        return {'data': output, 'paginated': dataUtils.get_paginated_list(outputs, pageData['offset'], pageData['limit'], pageData['page'])}
    else:
        return {'data': output, 'paginated': dataUtils.get_paginated_list(outputs, pageData['offset'], pageData['limit'], pageData['page'])}

@module.route('/data', methods=['POST'])
# @jwt_required()
@cross_origin()
def index():
    results = {}
    response = 500
    if request.method == 'POST':
        try:
            data = process_data(request)
            filterData = data['data']
            allData = data['paginated']
            
            if len(filterData) == 0:
                results['message'] = "Data not found!"
                results['status'] = "success"
                response = 200
            else:
                if 'limit' in request.form:
                    results['data'] = data['data']
                    results['meta'] = data['paginated']
                else:
                    results['data'] = data['data']
                results['message'] = "Data found!"
                results['status'] = "success"
                response = 200
        except Exception as e:
            print(e)
            results['message'] = "Internal Server Error!"
            results['status'] = "error"
            response = 500
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response

@module.route('/scoreboard', methods=['POST'])
@jwt_required()
@cross_origin()
def indexScoreBoard():
    results = {}
    response = 500
    if request.method == 'POST':
        try:
            data = process_data_scoreboard(request)
            filterData = data['data']
            allData = data['paginated']
            
            if len(filterData) == 0:
                results['message'] = "Data not found!"
                results['status'] = "success"
                response = 200
            else:
                if 'limit' in request.form:
                    results['data'] = data['data']
                    results['meta'] = data['paginated']
                else:
                    results['data'] = data['data']
                results['message'] = "Data found!"
                results['status'] = "success"
                response = 200
        except Exception as e:
            print(e)
            results['message'] = "Internal Server Error!"
            results['status'] = "error"
            response = 500
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response

@module.route('/store-review', methods=['POST'])
@jwt_required()
@cross_origin()
def storeFeedback():
    results = {}
    response = 500
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))[0]
        validation_result = validateForm(request, 'store_review')
        if validation_result.get('success', False) is True:
            try:
                moduleOrder = request.form['lesson'].split('-')
                findModule = list(moduleCollection.find({'order': int(moduleOrder[0])}).limit(1))
                print(len(findModule))
                if len(findModule) > 0:
                    findComment = list(moduleCollection.find({'order': int(moduleOrder[0]), 'comments.email': account['email']}).limit(1))
                    reviewData = {
                        "name": account['name'],
                        "email": account['email'],
                        "comment": request.form['comment'],
                        "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "rating": float(request.form['rating']),
                        "avatar": account['avatar'],
                    }
                    if len(findComment) > 0:
                        moduleCollection.update_one({
                            'order': int(moduleOrder[0])
                        }, {
                            "$set": {
                                'comments.$[comments]': reviewData
                            }
                        },
                        array_filters=[
                            {
                                "comments.email": {
                                    "$eq": account['email']
                                }
                            }
                        ])
                    else:
                        moduleCollection.update_one({
                            'order': int(moduleOrder[0])
                        }, {
                            "$push": {
                                'comments': reviewData
                            }
                        })
                results['message'] = "Review Saved!"
                results['status'] = "success"
                response = 201
            except Exception as e:
                print(e)
                results['message'] = "Internal Server Error!"
                results['status'] = "error"
                response = 500
        else:
            results['message'] = "Please check your input"
            results['status'] = 'error'
            results['errors'] = validation_result.get("error")
            response = 400
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response