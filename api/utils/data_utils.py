from flask import request
import pymongo

def validateForm(request, event, modulesPath):
    reqData = {}
    reqForm = request.form.to_dict(flat=False)
    for data in reqForm:
        reqData[data] = reqForm[data][0]
    if event == 'store':
        validation_result = modulesPath.createSchema.validate(reqData)
    elif event == 'update':
        validation_result = modulesPath.updateSchema.validate(reqData)
    elif event == 'delete':
        validation_result = modulesPath.deleteSchema.validate(reqData)
    return validation_result

def get_pagination_data(request, custom_order):
    data = {}
    if 'sort_by' in request.form and request.form['sort_by'] != '':
        data['sortBy'] = request.form['sort_by']
    elif 'sort_by' in custom_order and custom_order['sort_by'] != '':
        data['sortBy'] = custom_order['sort_by']
    else:
        data['sortBy'] = '_id'

    if 'order_by' in request.form and request.form['order_by'] == 'desc' and request.form['order_by'] != '':
        data['orderBy'] = pymongo.DESCENDING
    elif 'order_by' in custom_order and custom_order['order_by'] == 'desc' and custom_order['order_by'] != '':
        data['orderBy'] = pymongo.DESCENDING
    else:
        data['orderBy'] = pymongo.ASCENDING
        
    data['limit'] = int(
        request.form['limit']) if 'limit' in request.form and request.form['limit'] != '' and request.form != 0 else 10
    data['page'] = int(
        request.form['page']) if 'page' in request.form and request.form['page'] != '' and request.form != 0 else 1
    data['offset'] = (data['page'] * data['limit']) - data['limit']
    return data

def get_paginated_list(results, start, limit, current_page):
    start = int(start)
    limit = int(limit)
    count = len(results)
    obj = {}
    if count < start or limit < 0:
        obj['error'] = True
    # make response
    obj['start'] = start+1
    obj['limit'] = limit
    obj['count'] = count
    obj['current_page'] = current_page
    obj['first_page'] = 1
    obj['last_page'] = round(count/limit + 0.5) if count % 10 != 0 else round(count/limit)
    # make URLs
    # make previous url
    if current_page == 1:
        obj['previous_page'] = ''
    else:
        obj['previous_page'] = current_page - 1
    # make next url
    if start + limit >= count:
        obj['next_page'] = ''
    else:
        obj['next_page'] = current_page+1
    # finally extract result according to bounds
    # obj['results'] = results[(start):(start + limit)]
    return obj
