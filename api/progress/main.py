from flask import request
from api import db
from . import progress
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import re
import api.utils.data_utils as dataUtils
from bson.objectid import ObjectId

# initial db
progressDB = db.progress
accountCollection = db.accounts

def process_data(request, account):
    output = []
    outputs = []
    query = {}
    custom_order = {'sort_by': 'order'}
    pageData = dataUtils.get_pagination_data(request, custom_order)
    query['email'] = account[0]['email']
    
    # if 'search' in request.form and request.form['search'] != '' and request.form['search'] != 'null':
    #     query['email'] = re.compile(
    #         request.form['search'], re.IGNORECASE)
    # if 'find' in request.form and request.form['find'] != '' and request.form['find'] != 'null':
    #     query['_id'] = ObjectId(request.form['find'])
    # print(query)
    findData = progressDB.find(query).sort(pageData['sortBy'], pageData['orderBy']).skip(pageData['offset']).limit(pageData['limit'])
    findAllData = progressDB.find(query).sort(pageData['sortBy'], pageData['orderBy'])
    
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

@progress.route('/data', methods=['POST'])
@jwt_required()
@cross_origin()
def index():
    results = {}
    response = 500
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        if len(account) > 0:
            try:
                data = process_data(request, account)
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
            results['message'] = "Your account not found!"
            results['status'] = 'error'
            response = 403
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response