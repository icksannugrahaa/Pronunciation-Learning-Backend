from queue import Empty
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
moduleDB = db.modules
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
    findData = progressDB.find(query).sort(pageData['sortBy'], pageData['orderBy']).skip(
        pageData['offset']).limit(pageData['limit'])
    findAllData = progressDB.find(query).sort(
        pageData['sortBy'], pageData['orderBy'])

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

def findNextProgress(request):
    lessonSplit = request.form['lesson'].split('-')
    progressSplit = request.form['progress'].split('-')
                
    # set up next progress
    nextProgressData = {}
    tempNextProgressData = []
    nextProgress = {}
    query = {}

    nextModuleID = 1
    nextLessonID = int(lessonSplit[1])
    nextLessonType = "theory"
    nextLessonOrder = int(progressSplit[1])-1
    maxTries = 2

    nextProgressIsAvailable = True
    # check next must doing lesson
    while nextProgressIsAvailable and maxTries != 0:
        if progressSplit[0] == "t":
            nextLessonType = "theory"
            nextLessonOrder = nextLessonOrder+1
            query['lessons.theory.order'] = nextLessonOrder
        elif progressSplit[0] == "q":
            nextLessonType = "quiz"
            nextLessonOrder = nextLessonOrder+1
            query['lessons.quiz.order'] = nextLessonOrder
        elif progressSplit[0] == "s":
            nextLessonType = "summary"
            nextLessonOrder = 1
            nextLessonID = int(lessonSplit[1])+1
            query['lessons.order'] = nextLessonID
        else:
            nextModuleID = int(lessonSplit[0])+1
            nextLessonID = 1
            nextLessonType = "theory"
            nextLessonOrder = 1
            query['order'] = nextModuleID
        checkNextModule = list(moduleDB.find(query))
        # count module length
        if len(checkNextModule) > 0 and (nextModuleID-1) <= len(checkNextModule):
            # count lessons length
            if nextLessonID <= len(checkNextModule[nextModuleID-1]['lessons']):
                # count lesson material length
                if nextLessonOrder < len(checkNextModule[nextModuleID-1]['lessons'][nextLessonID-1][nextLessonType]) and nextLessonType != "summary":
                    nextProgressData = {
                        'lesson': request.form['lesson'],
                        'status': "new",
                        'progress': progressSplit[0]+"-"+str(int(progressSplit[1])+1),
                        'scores': None
                    }
                    nextProgressIsAvailable = False
                else:
                    if nextLessonType == "theory":
                        nextLessonType = "quiz"
                        nextLessonData = checkNextModule[nextModuleID-1]['lessons'][nextLessonID-1][nextLessonType]
                        if nextLessonData is not None:
                            nextProgressData = {
                                'lesson': request.form['lesson'],
                                'status': "new",
                                'progress': "q-1",
                                'scores': None
                            }
                            nextProgressIsAvailable = False
                        else:
                            nextProgressIsAvailable = False
                    elif nextLessonType == "quiz":
                        nextLessonType = "summary"
                        nextLessonData = checkNextModule[nextModuleID-1]['lessons'][nextLessonID-1][nextLessonType]
                        if nextLessonData is not None:
                            nextProgressData = {
                                'lesson': request.form['lesson'],
                                'status': "new",
                                'progress': "s-1",
                                'scores': None
                            }
                            nextProgressIsAvailable = False
                        else:
                            nextProgressData = {
                                'lesson': str(lessonSplit[0])+"-"+str(int(lessonSplit[1])+1),
                                'status': "new",
                                'progress': "t-1",
                                'scores': None
                            }
                            nextProgress = {
                                'order': lessonSplit[0],
                                'currentProgress': str(lessonSplit[0])+"-"+str(int(lessonSplit[1])+1)+"-t-1",
                                'status': "new",
                                'progress': tempNextProgressData
                            }
                            nextProgressIsAvailable = False
                    else:
                        nextProgressData = {
                            'lesson': str(lessonSplit[0])+"-"+str(int(lessonSplit[1])+1),
                            'status': "new",
                            'progress': "t-1",
                            'scores': None
                        }
                        nextProgress = {
                            'order': lessonSplit[0],
                            'currentProgress': str(lessonSplit[0])+"-"+str(int(lessonSplit[1])+1)+"-t-1",
                            'status': "new",
                            'progress': tempNextProgressData
                        }
                        nextProgressIsAvailable = False
            else:
                nextProgressIsAvailable = False
        else:
            query['order'] = nextModuleID+1
            query['lessons.order'] = 1
            query['lessons.theory.order'] = 1
            checkNextModule = list(moduleDB.find(query))
            nextModule = checkNextModule[0]['lessons'][1]['theory'][1]
            if nextModule is not None:
                nextProgressData = {
                    'lesson': str(int(lessonSplit[0])+1)+"-1",
                    'status': "new",
                    'progress': "t-1",
                    'scores': None
                }
                nextProgress = {
                    'order': int(lessonSplit[0])+1,
                    'currentProgress': str(int(lessonSplit[0])+1)+"-1-t-1",
                    'status': "new",
                    'progress': tempNextProgressData
                }
                nextProgressIsAvailable = False
            else:
                nextProgressIsAvailable = False  
    return {'progressData': nextProgressData, 'progress': nextProgress}

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


@progress.route('/store', methods=['POST'])
@jwt_required()
@cross_origin()
def store():
    results = {}
    response = 500
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        if len(account) > 0:
            try:
                # init
                lessonSplit = request.form['lesson'].split('-')
                progressSplit = request.form['progress'].split('-')
                scoreCode = request.form['progress']+"-" + \
                    request.form['score']+"-"+request.form['time']
                currentProgressCode = request.form['lesson'] + \
                    "-"+request.form['progress']

                # data
                lastLearn = {
                    'lesson': request.form['lesson'],
                    'status': "in_progress"
                }

                tempScoreData = []
                tempScoreData.append(scoreCode)
                scoreData = {
                    'time': request.form['time'],
                    'score': request.form['score'],
                    'scoreDetail': tempScoreData
                }

                progressData = {
                    'lesson': request.form['lesson'],
                    'status': request.form['status'],
                    'progress': request.form['progress'],
                    'scores': scoreData
                }

                tempprogressData = []
                tempprogressData.append(progressData)

                currentProgress = {
                    'order': int(lessonSplit[0]),
                    'currentProgress': currentProgressCode,
                    'status': "in_progress",
                    'progress': tempprogressData
                }

                # Check current module is available ?
                query = {}
                query['order'] = int(lessonSplit[0])
                query['lessons.order'] = int(lessonSplit[1])
                if progressSplit[0] == "t":
                    query['lessons.theory.order'] = int(progressSplit[1])
                elif progressSplit[0] == "q":
                    query['lessons.quiz.order'] = int(progressSplit[1])

                checkCurrentModule = list(moduleDB.find(query))

                if len(checkCurrentModule) > 0:
                    # check progress is never save before ?
                    progressIsAvailable = list(
                        progressDB.find({'email': currentAccount}))
                    
                     # find next progress    
                    progress = findNextProgress(request)
                    nextProgressData = progress['progressData']
                    nextProgress = progress['progress']
                    tempNextProgressData = [] 
                    tempNextProgressData.append(nextProgressData)
                    
                    print(nextProgressData)
                    print(nextProgress)
                    print(tempNextProgressData)
                    if len(progressIsAvailable) > 0:
                        print('masuk sini 1')
                        #check how much this account doing progress
                        if len(progressIsAvailable[0]['allProgress']) > 0:
                            print('masuk sini 2')
                            for iprogres, progress in enumerate(progressIsAvailable[0]['allProgress']):
                                print(iprogres)
                                print(progressIsAvailable[0]['allProgress'])
                                # check if this account have doing this lesson before
                                if progress['order'] == int(lessonSplit[0]):
                                    print('masuk sini 4')
                                    # check if this account have doing progress ?
                                    if len(progress['progress']) > 0:
                                        for progressItem in progress['progress']:
                                            if progressItem['lesson'] == request.form['lesson'] and progressItem['progress'] == request.form['progress'] and progressItem['status'] != 'done':
                                                print('masuk sini 5')
                                                progressDB.update_one(
                                                    {
                                                        'email': currentAccount
                                                    },
                                                    {
                                                        "$set": {
                                                            'lastLearn': lastLearn,
                                                            'allProgress.$[module].currentProgress': currentProgressCode,
                                                            'allProgress.$[module].status': "done" if progressSplit[0] == "s" else "in_progress",
                                                            'allProgress.$[module].progress.$[lesson]': progressData
                                                        }
                                                    },
                                                    array_filters= [
                                                        {
                                                            "module.order": {
                                                                "$eq": int(lessonSplit[0])
                                                            }
                                                        },
                                                        {
                                                            "lesson.progress": {
                                                                "$eq": request.form['progress']
                                                            },
                                                            "lesson.lesson": {
                                                                "$eq": request.form['lesson']
                                                            }
                                                        }
                                                    ]
                                                )
                                                if nextProgressData and progressSplit[0] != "s":
                                                    print('masuk sini 6')
                                                    progressDB.update_one(
                                                        {
                                                            'email': currentAccount
                                                        },
                                                        {
                                                            "$push": {
                                                                'allProgress.$[module].progress': nextProgressData
                                                            }
                                                        },
                                                        upsert= False,
                                                        array_filters= [
                                                            {
                                                                "module.order": {
                                                                    "$eq": int(lessonSplit[0])
                                                                }
                                                            }
                                                        ]
                                                    )
                                                    break
                                                elif nextProgressData and progressSplit[0] == "s" and lessonSplit[0] == nextProgressData['lesson'].split('-')[0]:
                                                    print('masuk sini 6')
                                                    progressDB.update_one(
                                                        {
                                                            'email': currentAccount
                                                        },
                                                        {
                                                            "$push": {
                                                                'allProgress.$[module].progress': nextProgressData
                                                            }
                                                        },
                                                        upsert= False,
                                                        array_filters= [
                                                            {
                                                                "module.order": {
                                                                    "$eq": int(lessonSplit[0])
                                                                }
                                                            }
                                                        ]
                                                    )
                                                else:
                                                    print('masuk sini 7')
                                                    tempNextProgressData.append(nextProgressData)
                                                    nextProgress['progress'] = tempNextProgressData
                                                    progressDB.update_one(
                                                        {
                                                            'email': currentAccount
                                                        },
                                                        {
                                                            "$push": {
                                                                'allProgress': nextProgress
                                                            }
                                                        }
                                                    )
                                    break
                                elif iprogres == len(progressIsAvailable[0]['allProgress'])-1:
                                    print('masuk sini 5')
                                    tempprogressData.append(nextProgressData)
                                    progressDB.update_one(
                                        {
                                            'email': currentAccount
                                        },
                                        {
                                            "$set": {
                                                'lastLearn': lastLearn
                                            },
                                            "$push": {
                                                'allProgress': currentProgress   
                                            }
                                        }
                                    )
                        else:
                            print('masuk sini 3')
                            if request.form['status'] == "done":
                                tempprogressData.append(nextProgressData)
                            progressDB.update_one(
                                {'email': currentAccount},
                                {
                                    "$set": {
                                        'lastLearn': lastLearn
                                    },
                                    "$push": {
                                        'allProgress': currentProgress
                                    }
                                }
                            )
                    else:
                        if request.form['status'] == "done":
                            currentProgress['progress'].append(nextProgressData)
                        progressDB.insert_one({
                            "email": currentAccount,
                            "lastLearn": lastLearn,
                            "allProgress": [currentProgress]
                        })
                        print('progress 3')

                    results['message'] = "Data successfully saved!"
                    results['status'] = "success"
                    response = 200
                else:
                    results['message'] = "Module not found!"
                    results['status'] = "error"
                    response = 200

            except Exception as e:
                print(e)
                results['message'] = "Internal Server Error!"
                results['status'] = "error"
                results['error'] = str(e)
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
