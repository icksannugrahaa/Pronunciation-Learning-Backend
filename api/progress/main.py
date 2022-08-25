from queue import Empty
from flask import request
from api import db
from . import progress
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import re
import api.utils.data_utils as dataUtils
from bson.objectid import ObjectId
import datetime
import api.utils.achievement_utils as achievementUtils 

# initial db
progressDB = db.progress
moduleDB = db.modules
accountCollection = db.accounts
levelCollection = db.levels
scoreboardCollection = db.scoreboards


def process_data(request, account):
    output = []
    outputs = []
    query = {}
    custom_order = {'sort_by': 'order'}
    pageData = dataUtils.get_pagination_data(request, custom_order)
    query['email'] = account[0]['email']
    print(request.form)
    # if 'search' in request.form and request.form['search'] != '' and request.form['search'] != 'null':
    #     query['email'] = re.compile(
    #         request.form['search'], re.IGNORECASE)
    if 'find' in request.form and request.form['find'] != '' and request.form['find'] != 'null':
        lessonSplit = request.form['find'].split('-')
        print(lessonSplit)
        query['allProgress.order'] = {"$eq": int(lessonSplit[0])}
        # query['progress.lesson'] = request.form['lesson']
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
                        nextLessonData = checkNextModule[nextModuleID -
                                                         1]['lessons'][nextLessonID-1][nextLessonType]
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
                        nextLessonData = checkNextModule[nextModuleID -
                                                         1]['lessons'][nextLessonID-1][nextLessonType]
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


def checkNextProgress(moduleOrder, lessonOrder, progress):
    query = {}
    query['order'] = moduleOrder
    query['lessons.order'] = lessonOrder
    print(query)
    nextData = {}
    progressSplit = progress.split('-')
    checkNextModule = list(moduleDB.find(query).limit(1))
    # print(len(checkNextModule))
    if len(checkNextModule) > 0:
        checkNextModuleData = checkNextModule[0] 
        lesson = [p for p in checkNextModuleData['lessons'] if p['order'] == lessonOrder]
        if len(lesson) > 0:
            currentLesson = lesson[0]
            typeLesson = "theory" if progressSplit[0] == "t" else "quiz" if progressSplit[0] == "q" else "summary"
            print(typeLesson)
            if typeLesson == "summary":
                if "summary" in currentLesson and currentLesson['summary']['title'] != "":
                    nextData = {
                        'lesson': str(moduleOrder)+"-"+str(lessonOrder),
                        'status': "new",
                        'progress': progress,
                        'scores': None
                    }
            else:  
                if len(currentLesson[typeLesson]) > 0:
                    for lessonData in currentLesson[typeLesson]:
                        lessonProgress = progressSplit[0]+"-"+str(lessonData['order'])
                        print(lessonProgress+"=="+progress)
                        if lessonProgress == progress:
                            nextData = {
                                'lesson': str(moduleOrder)+"-"+str(lessonOrder),
                                'status': "new",
                                'progress': progress,
                                'scores': None
                            }
                            break
    print(nextData)
            
    return nextData

def findNext(request):
    lessonSplit = request.form['lesson'].split('-')
    progressSplit = request.form['progress'].split('-')
    
    # init next progress
    nextProgressData = {}
    tempNextProgressData = []
    nextProgress = {}
    nextProgressIsAvailable = True
    
    while(nextProgressIsAvailable):
        if progressSplit[0] == 't':
            moduleID = int(lessonSplit[0])
            lessonID = int(lessonSplit[1])
            nextProgressCode = progressSplit[0]+"-"+str(int(progressSplit[1])+1)
            nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
            if nextProgress:
                nextProgressIsAvailable = False
            else:
                nextProgressCode = "q-1"
                nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                if nextProgress:
                    nextProgressIsAvailable = False
                else:
                    nextProgressCode = "s-1"
                    nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                    if nextProgress:
                        nextProgressIsAvailable = False
                    else:
                        nextProgressIsAvailable = False
        elif progressSplit[0] == 'q':
            moduleID = int(lessonSplit[0])
            lessonID = int(lessonSplit[1])
            nextProgressCode = progressSplit[0]+"-"+str(int(progressSplit[1])+1)
            nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
            if nextProgress:
                nextProgressIsAvailable = False
            else:
                nextProgressCode = "s-1"
                nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                if nextProgress:
                    nextProgressIsAvailable = False
                else:
                    lessonID = int(lessonSplit[1])+1
                    nextProgressCode = "t-1"
                    nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                    if nextProgress:
                        nextProgressIsAvailable = False
                    else:
                        moduleID = int(lessonSplit[0])+1
                        lessonID = 1
                        nextProgressCode = "t-1"
                        nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                        if nextProgress:
                            nextProgressData = {
                                'order': lessonID,
                                'currentProgress': str(moduleID)+"-1-t-1",
                                'status': "new",
                                'progress': tempNextProgressData
                            }
                            nextProgressIsAvailable = False
                        else:
                            nextProgressIsAvailable = False
        elif progressSplit[0] == 's':
            moduleID = int(lessonSplit[0])
            lessonID = int(lessonSplit[1])+1
            nextProgressCode = "t-1"
            nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
            if nextProgress:
                nextProgressIsAvailable = False
            else:
                moduleID = int(lessonSplit[0])+1
                lessonID = 1
                nextProgressCode = "t-1"
                nextProgress = checkNextProgress(moduleID, lessonID, nextProgressCode)
                if nextProgress:
                    nextProgressData = {
                        'order': lessonID,
                        'currentProgress': str(moduleID)+"-1-t-1",
                        'status': "new",
                        'progress': tempNextProgressData
                    }
                    nextProgressIsAvailable = False
                else:
                    nextProgressIsAvailable = False
        nextProgressIsAvailable = False    
    return {'progress': nextProgress, 'progressData': nextProgressData}       


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

                scoreData = {
                    'time': request.form['time'],
                    'score': request.form['score'],
                    'quest': request.form['quest'],
                    'answer': request.form['answer'],
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
                    
                # print(query)

                checkCurrentModule = list(moduleDB.find(query))
                # print(len(checkCurrentModule))

                if len(checkCurrentModule) > 0:
                    # check progress is never save before ?
                    progressIsAvailable = list(
                        progressDB.find({'email': currentAccount}))

                    # find next progress
                    progress = findNext(request)
                    nextProgressData = progress['progress']
                    nextProgress = progress['progressData']
                    tempNextProgressData = []
                    tempNextProgressData.append(nextProgressData)

                    print(nextProgressData)
                    print(nextProgress)
                    # print(tempNextProgressData)
                    if len(progressIsAvailable) > 0:
                        print('masuk sini 1')
                        # check how much this account doing progress
                        if len(progressIsAvailable[0]['allProgress']) > 0:
                            print('masuk sini 2')
                            for iprogres, progress in enumerate(progressIsAvailable[0]['allProgress']):
                                print(iprogres)
                                # print(progressIsAvailable[0]['allProgress'])
                                # check if this account have doing this lesson before
                                if progress['order'] == int(lessonSplit[0]):
                                    print('masuk sini 4')
                                    # check if this account have doing progress ?
                                    if len(progress['progress']) > 0:
                                        for progressItem in progress['progress']:
                                            print(progressItem)
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
                                                            'allProgress.$[module].status': "done" if progressSplit[0] == "s" and not nextProgress and not nextProgressData or progressSplit[0] == "s" and nextProgressData and lessonSplit[0] != nextProgressData['lesson'].split('-')[0] else "in_progress",
                                                            'allProgress.$[module].progress.$[lesson]': progressData
                                                        }
                                                    },
                                                    array_filters=[
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
                                                print('masuk sini 5.1')
                                                
                                                results['levelUp'] = False
                                                results['newAchievement'] = False
                                                
                                                if progressSplit[0] == "t":
                                                    # check new achievement theory
                                                    newAchivementTheory = achievementUtils.checkAchievementTheory(currentAccount)
                                                    if newAchivementTheory['status'] == 'success':
                                                        results['levelUp'] = True if results['levelUp'] == True or newAchivementTheory['levelUp'] == True else False
                                                        results['newAchievement'] = True if results['newAchievement'] == True or newAchivementTheory['status'] == 'success' else False
                                                        results['newAchievementMsg'] = newAchivementTheory['message']
                                                    else:
                                                        results['levelUp'] = True if results['levelUp'] == True or newAchivementTheory['levelUp'] == True else False
                                                        results['newAchievement'] = True if results['newAchievement'] == True or newAchivementTheory['status'] == 'success' else False
                                                        results['newAchievementMsg'] = "New Achievement Archived!" if results['newAchievement'] == True else newAchivementTheory['message']
                                                if progressSplit[0] == "q":  
                                                    # check new achievement quizz
                                                    newAchivementQuizz = achievementUtils.checkAchievementQuizz(currentAccount)
                                                    if newAchivementQuizz['status'] == 'success':
                                                        results['levelUp'] = True if results['levelUp'] == True or newAchivementQuizz['levelUp'] == True else False
                                                        results['newAchievement'] = True if results['newAchievement'] == True or newAchivementQuizz['status'] == 'success' else False
                                                        results['newAchievementMsg'] = newAchivementQuizz['message']
                                                    else:
                                                        results['levelUp'] = True if results['levelUp'] == True or newAchivementQuizz['levelUp'] == True else False
                                                        results['newAchievement'] = True if results['newAchievement'] == True or newAchivementQuizz['status'] == 'success' else False
                                                        results['newAchievementMsg'] = "New Achievement Archived!" if results['newAchievement'] == True else newAchivementTheory['message']
                                                    
                                                if nextProgressData and progressSplit[0] != "s":
                                                    print('masuk sini 7')
                                                    progressDB.update_one(
                                                        {
                                                            'email': currentAccount
                                                        },
                                                        {
                                                            "$push": {
                                                                'allProgress.$[module].progress': nextProgressData
                                                            }
                                                        },
                                                        upsert=False,
                                                        array_filters=[
                                                            {
                                                                "module.order": {
                                                                    "$eq": int(lessonSplit[0])
                                                                }
                                                            }
                                                        ]
                                                    )
                                                    break
                                                elif nextProgressData and progressSplit[0] == "s" and lessonSplit[0] == nextProgressData['lesson'].split('-')[0]:
                                                    print('masuk sini 8')
                                                    print(account[0]['exp'])

                                                    # update exp
                                                    lessonExp = checkCurrentModule[0]['lessons'][int(
                                                        lessonSplit[1])-1]['exp']
                                                    currentExp = account[0]['exp'] + lessonExp
                                                    levelFind = list(levelCollection.find({'exp': {
                                                        "$gte": currentExp
                                                    }}).limit(2))
                                                    
                                                    newLevel = 0
                                                    newExp = 0
                                                    newExpNext = 0
                                                    newLevelName = 'Beginner'
                                                    if currentExp > account[0]['exp']:
                                                        newExp = currentExp
                                                        if currentExp >= levelFind[0]['exp']:
                                                            newLevel = int(levelFind[0]['level'])
                                                            newExpNext = int(levelFind[1]['exp']) if len(levelFind) > 1 else 99999999
                                                            newLevelName = levelFind[0]['name']
                                                            results['levelUp'] = True
                                                        else:
                                                            newLevel = int(account[0]['level'])
                                                            newExpNext = int(account[0]['expNext'])
                                                            newLevelName = account[0]['levelName']
                                                            
                                                    accountCollection.update_one({
                                                        "email": currentAccount
                                                    },
                                                    {
                                                        "$set": {
                                                            "exp": newExp,
                                                            "level": newLevel,
                                                            "expNext": newExpNext,
                                                            "levelName": newLevelName
                                                        }       
                                                    })
                                                        
                                                    # save to scoreboard
                                                    checkScoreBoard = list(scoreboardCollection.find({'email': currentAccount, 'lesson': request.form['lesson']}))
                                                    scoreboardData = {
                                                        "name": account[0]['name'],
                                                        "score": float(request.form['score']),
                                                        "time": int(request.form['time']),
                                                        "email": account[0]['email'],
                                                        "avatar": account[0]['avatar'],
                                                        "lesson": request.form['lesson'],
                                                        "createdAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                    }
                                                    if len(checkScoreBoard) > 0:
                                                        scoreboardCollection.update_one({
                                                            'email': currentAccount,
                                                            'lesson': request.form['lesson']
                                                        },
                                                        {
                                                            '$set': scoreboardData
                                                        })
                                                    else:
                                                        scoreboardCollection.insert_one(scoreboardData)

                                                    # update progress + next progress
                                                    progressDB.update_one(
                                                        {
                                                            'email': currentAccount
                                                        },
                                                        {
                                                            "$push": {
                                                                'allProgress.$[module].progress': nextProgressData
                                                            }
                                                        },
                                                        upsert=False,
                                                        array_filters=[
                                                            {
                                                                "module.order": {
                                                                    "$eq": int(lessonSplit[0])
                                                                }
                                                            }
                                                        ]
                                                    )
                                                else:
                                                    print(checkCurrentModule[0]['lessons'])
                                                    print('masuk sini 9')
                                                    # update exp
                                                    lessonExp = checkCurrentModule[0]['lessons'][int(
                                                        lessonSplit[1])-1]['exp']
                                                    print(lessonExp)
                                                    currentExp = account[0]['exp'] + lessonExp
                                                    print(currentExp)
                                                    levelFind = list(levelCollection.find({'exp': {
                                                        "$gte": currentExp
                                                    }}).limit(2))
                                                    
                                                    newLevel = 0
                                                    newExp = 0
                                                    newExpNext = 0
                                                    newLevelName = 'Beginner'
                                                    if currentExp > account[0]['exp']:
                                                        newExp = currentExp
                                                        if currentExp >= levelFind[0]['exp']:
                                                            newLevel = int(levelFind[0]['level'])
                                                            newExpNext = int(levelFind[1]['exp']) if len(levelFind) > 1 else 99999999
                                                            newLevelName = levelFind[0]['name']
                                                            results['levelUp'] = True
                                                        else:
                                                            newLevel = int(account[0]['level'])
                                                            newExpNext = int(account[0]['expNext'])
                                                            newLevelName = account[0]['levelName']
                                                            
                                                    accountCollection.update_one({
                                                        "email": currentAccount
                                                    },
                                                    {
                                                        "$set": {
                                                            "exp": newExp,
                                                            "level": newLevel,
                                                            "expNext": newExpNext,
                                                            "levelName": newLevelName
                                                        }       
                                                    })
                                                        
                                                    # save to scoreboard
                                                    checkScoreBoard = list(scoreboardCollection.find({'email': currentAccount, 'lesson': request.form['lesson']}))
                                                    scoreboardData = {
                                                        "name": account[0]['name'],
                                                        "score": float(request.form['score']),
                                                        "time": int(request.form['time']),
                                                        "email": account[0]['email'],
                                                        "avatar": account[0]['avatar'],
                                                        "lesson": request.form['lesson'],
                                                        "createdAt": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                                    }
                                                    if len(checkScoreBoard) > 0:
                                                        scoreboardCollection.update_one({
                                                            'email': currentAccount,
                                                            'lesson': request.form['lesson']
                                                        },
                                                        {
                                                            '$set': scoreboardData
                                                        })
                                                    else:
                                                        scoreboardCollection.insert_one(scoreboardData)

                                                    # update progress + next progress
                                                    if nextProgress:
                                                        nextProgressID = nextProgress['currentProgress'].split('-')
                                                        checkProgress = checkNextProgress(int(nextProgressID[0]), int(nextProgressID[1]), nextProgressID[2]+"-"+nextProgressID[3])
                                                        if not checkProgress:
                                                            tempNextProgressData.append(
                                                                nextProgressData)
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
                                    print('masuk sini 55')
                                    if nextProgressData:
                                        tempprogressData.append(nextProgressData)
                                        print('masuk sini 5.1')
                                    print('masuk sini 5.2')
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
                                    print('masuk sini 5.3')
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
                            currentProgress['progress'].append(
                                nextProgressData)
                        progressDB.insert_one({
                            "email": currentAccount,
                            "lastLearn": lastLearn,
                            "allProgress": [currentProgress]
                        })
                        print('progress 3')

                    results['message'] = "Data successfully saved!"
                    results['status'] = "success"
                    results['levelUp'] = False if "levelUp" not in results else results['levelUp']
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
