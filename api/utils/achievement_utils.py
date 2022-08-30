from flask import request
import pymongo
from api import db
import datetime


achievementCollection = db.achievements
accountCollection = db.accounts
progressCollection = db.progress
levelCollection = db.levels

def updateExp(exp, email):
    #init data
    account = list(accountCollection.find({'email': email}))
    levelUp = False
    
    # prepare update exp
    currentExp = account[0]['exp'] + exp
    levelFind = list(levelCollection.find({'exp': {
        "$gte": account[0]['exp']
    }}).limit(2))
    print(levelFind)
    print(currentExp)
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
            levelUp = True
        else:
            newLevel = int(account[0]['level'])
            newExpNext = int(account[0]['expNext'])
            newLevelName = account[0]['levelName']
    
    #update account exp
    accountCollection.update_one({
        "email": email
    },
    {
        "$set": {
            "exp": newExp,
            "level": newLevel,
            "expNext": newExpNext,
            "levelName": newLevelName
        }       
    })
    
    return levelUp

def checkAchievementTheory(email):
    newAchievement = {}
    account = list(accountCollection.find({'email': email}))
    if len(account) > 0:
        try:
            progressData = list(progressCollection.find({'email': email}))
            print("achievement 3")
            if len(progressData) > 0:
                print("achievement 4")
                if len(progressData[0]['allProgress']) > 0:
                    print("achievement 5")
                    #init data
                    progressDone = 0
                    newArchived = {}
                    dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for progress in progressData[0]['allProgress']:
                        print("achievement 6")
                        if len(progress['progress']) > 0:
                            print("achievement 7")
                            # check progress
                            for progressItem in progress['progress']:
                                
                                print("achievement 7.1")
                                # print(progressItem)
                                if 'progress' in progressItem:
                                    progressType = progressItem['progress'].split("-")[0]
                                    if progressType == "t" and progressItem['status'] == "done":
                                        progressDone += 1
                                else:
                                    break
                            print("achievement 12")   
                            
                    # find achievement
                    achievementData = list(achievementCollection.find({'name': "Theory Achievement"}).limit(1))
                    
                    print("achievement 13")
                    
                    # check user achievement
                    if len(account[0]['achievement']) > 0:
                        print("achievement 1")
                        newLevel = {}
                        expEarned = 0
                        if len(achievementData) > 0:
                            userAchievementFilter = [p for p in account[0]['achievement'] if p['name'] == achievementData[0]['name']]
                            if len(userAchievementFilter) > 0:
                                userAchievement = userAchievementFilter[0]
                                # print(userAchievement)
                                userAchievementLevel = userAchievement['level']
                                userLastLevel = userAchievement['level'][len(userAchievementLevel)-1]['level']
                                print(userLastLevel)
                                for achievement in achievementData[0]['level']:
                                    if progressDone == achievement['requirements']['theory']:
                                        print("MASUK NEW ACHIEVEMENT")
                                        if  achievement['level'] >= userLastLevel:
                                            newLevel = {
                                                "name": achievement['name'],
                                                "description": achievement['description'],
                                                "level": achievement['level'],
                                                "createdAt": dateNow
                                            }
                                            expEarned = achievement['exp']
                                            break
                            else:
                                newLevel = {
                                    "name": achievementData[0]['level'][0]['name'],
                                    "description": achievementData[0]['level'][0]['description'],
                                    "level": achievementData[0]['level'][0]['level'],
                                    "createdAt": dateNow
                                }
                                expEarned = achievement['exp']
                            if bool(newLevel):
                                print("MASUK UPDATE ACHIEVEMENT")
                                
                                accountCollection.update_one(
                                    {
                                        "email": email,
                                        "achievement.name": achievementData[0]['name']
                                    },
                                    {
                                        "$push": {
                                            'achievement.$.level': newLevel
                                        }
                                    }
                                )
                                newAchievement['levelUp'] = updateExp(expEarned, email)
                                newAchievement['message'] = "New Achievement Archived!"
                                newAchievement['status'] = "success"
                            else:
                                print("GA MASUK UPDATE ACHIEVEMENT")
                                newAchievement['levelUp'] = False
                                newAchievement['message'] = "No Achievement Archived!"
                                newAchievement['status'] = "error"
                        else:
                            newAchievement['levelUp'] = False
                            newAchievement['message'] = "No Achievement Archived!"
                            newAchievement['status'] = "error"
                    else:
                        print("achievement 2")
                        expEarned = 0
                        newArchived = {
                            'name': achievementData[0]['name'],
                            'level': []
                        }
                        for achievement in achievementData[0]['level']:
                            print(str(progressDone)+" - "+str(achievement['requirements']['theory']))
                            if progressDone == achievement['requirements']['theory']:
                                print("achievement 2.1")
                                newArchived['level'].append({
                                    "name": achievement['name'],
                                    "description": achievement['description'],
                                    "level": achievement['level'],
                                    "createdAt": dateNow
                                })
                                expEarned = achievement['exp']
                                break
                            print("achievement 2.2")
                        accountCollection.update_one(
                            {"email": email},
                            {
                                "$push": {
                                    'achievement': newArchived
                                }
                            }
                        )
                        newAchievement['levelUp'] = updateExp(expEarned, email)
                        newAchievement['message'] = "New Achievement Archived!"
                        newAchievement['status'] = "success"
                else:
                    print("achievement 9")
                    newAchievement['message'] = "No Achievement Archived!"
                    newAchievement['status'] = "error"
            else:
                print("achievement 10")
                newAchievement['message'] = "No Achievement Archived!"
                newAchievement['status'] = "error"
        except Exception as e:
            print(e)
            print("achievement 11")
            newAchievement['message'] = "Internal Server Error!"
            newAchievement['status'] = "error"
    else:
        newAchievement['message'] = "Your account not found!"
        newAchievement['status'] = 'error'

    return newAchievement

def checkAchievementQuizz(email):
    newAchievement = {}
    account = list(accountCollection.find({'email': email}))
    if len(account) > 0:
        try:
            progressData = list(progressCollection.find({'email': email}))
            print("achievement 3")
            if len(progressData) > 0:
                print("achievement 4")
                if len(progressData[0]['allProgress']) > 0:
                    print("achievement 5")
                    #init data
                    progressDone = 0
                    newArchived = {}
                    dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for progress in progressData[0]['allProgress']:
                        print("achievement 6")
                        if len(progress['progress']) > 0:
                            print("achievement 7")
                            # check progress
                            for progressItem in progress['progress']:
                                
                                print("achievement 7.1")
                                # print(progressItem)
                                if 'progress' in progressItem:
                                    progressType = progressItem['progress'].split("-")[0]
                                    if progressType == "q" and progressItem['status'] == "done":
                                        progressDone += 1
                                else:
                                    break
                            print("achievement 12")   
                            
                    # find achievement
                    achievementData = list(achievementCollection.find({'name': "Quizz Achievement"}).limit(1))
                    
                    print("achievement 13")
                    
                    # check user achievement
                    if len(account[0]['achievement']) > 0:
                        print("achievement 1")
                        newLevel = {}
                        expEarned = 0
                        isUpdate = False
                        if len(achievementData) > 0:
                            userAchievementFilter = [p for p in account[0]['achievement'] if p['name'] == achievementData[0]['name']]
                            if len(userAchievementFilter) > 0:
                                userAchievement = userAchievementFilter[0]
                                # print(userAchievement)
                                userAchievementLevel = userAchievement['level']
                                userLastLevel = userAchievement['level'][len(userAchievementLevel)-1]['level']
                                print(userLastLevel)
                                for achievement in achievementData[0]['level']:
                                    if progressDone == achievement['requirements']['quizz']:
                                        print("MASUK NEW ACHIEVEMENT")
                                        if  achievement['level'] >= userLastLevel:
                                            newLevel = {
                                                "name": achievement['name'],
                                                "description": achievement['description'],
                                                "level": achievement['level'],
                                                "createdAt": dateNow
                                            }
                                            expEarned = achievement['exp']
                                            break
                            else:
                                isUpdate = True
                                newLevel = {
                                    "name": achievementData[0]['level'][0]['name'],
                                    "description": achievementData[0]['level'][0]['description'],
                                    "level": achievementData[0]['level'][0]['level'],
                                    "createdAt": dateNow
                                }
                                expEarned = achievementData[0]['level'][0]['exp']
                            if bool(newLevel):
                                print("MASUK UPDATE ACHIEVEMENT")
                                if isUpdate:
                                    newArchived = {
                                        'name': achievementData[0]['name'],
                                        'level': []
                                    }
                                    newArchived['level'].append(newLevel)
                                    accountCollection.update_one(
                                        {"email": email},
                                        {
                                            "$push": {
                                                'achievement': newArchived
                                            }
                                        }
                                    )
                                else:
                                    accountCollection.update_one(
                                        {
                                            "email": email,
                                            "achievement.name": achievementData[0]['name']
                                        },
                                        {
                                            "$push": {
                                                'achievement.$.level': newLevel
                                            }
                                        }
                                    )
                                newAchievement['levelUp'] = updateExp(expEarned, email)
                                newAchievement['message'] = "New Achievement Archived!"
                                newAchievement['status'] = "success"
                            else:
                                print("GA MASUK UPDATE ACHIEVEMENT")
                                newAchievement['levelUp'] = False
                                newAchievement['message'] = "No Achievement Archived!"
                                newAchievement['status'] = "error"
                        else:
                            newAchievement['levelUp'] = False
                            newAchievement['message'] = "No Achievement Archived!"
                            newAchievement['status'] = "error"
                    else:
                        print("achievement 2")
                        expEarned = 0
                        newArchived = {
                            'name': achievementData[0]['name'],
                            'level': []
                        }
                        for achievement in achievementData[0]['level']:
                            if progressDone == achievement['requirements']['quizz']:
                                newArchived['level'].append({
                                    "name": achievement['name'],
                                    "description": achievement['description'],
                                    "level": achievement['level'],
                                    "createdAt": dateNow
                                })
                                expEarned = achievement['exp']
                                break
                        
                        accountCollection.update_one(
                            {"email": email},
                            {
                                "$push": {
                                    'achievement': newArchived
                                }
                            }
                        )
                        newAchievement['levelUp'] = updateExp(expEarned, email)
                        newAchievement['message'] = "New Achievement Archived!"
                        newAchievement['status'] = "success"
                else:
                    print("achievement 9")
                    newAchievement['message'] = "No Achievement Archived!"
                    newAchievement['status'] = "error"
            else:
                print("achievement 10")
                newAchievement['message'] = "No Achievement Archived!"
                newAchievement['status'] = "error"
        except Exception as e:
            print(e)
            print("achievement 11")
            newAchievement['message'] = "Internal Server Error!"
            newAchievement['status'] = "error"
    else:
        newAchievement['message'] = "Your account not found!"
        newAchievement['status'] = 'error'

    return newAchievement

def checkAchievementLevel(email):
    newAchievement = {}
    account = list(accountCollection.find({'email': email}))
    if len(account) > 0:
        try:
            dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # find achievement
            achievementData = list(achievementCollection.find({'name': "Level Achievement"}).limit(1))
            
            # check user achievement
            if len(account[0]['achievement']) > 0:
                print("achievement 1")
                newLevel = {}
                expEarned = 0
                isUpdate = False
                if len(achievementData) > 0:
                    userAchievementFilter = [p for p in account[0]['achievement'] if p['name'] == achievementData[0]['name']]
                    if len(userAchievementFilter) > 0:
                        userAchievement = userAchievementFilter[0]
                        # print(userAchievement)
                        userAchievementLevel = userAchievement['level']
                        userLastLevel = userAchievement['level'][len(userAchievementLevel)-1]['level']
                        print(userLastLevel)
                        for achievement in achievementData[0]['level']:
                            if account[0]['level'] == achievement['requirements']['level']:
                                print("MASUK NEW ACHIEVEMENT")
                                if  achievement['level'] >= userLastLevel:
                                    newLevel = {
                                        "name": achievement['name'],
                                        "description": achievement['description'],
                                        "level": achievement['level'],
                                        "createdAt": dateNow
                                    }
                                    expEarned = achievement['exp']
                                    break
                    else:
                        isUpdate = True
                        newLevel = {
                            "name": achievementData[0]['level'][0]['name'],
                            "description": achievementData[0]['level'][0]['description'],
                            "level": achievementData[0]['level'][0]['level'],
                            "createdAt": dateNow
                        }
                        expEarned = achievementData[0]['level'][0]['exp']
                    if bool(newLevel):
                        print("MASUK UPDATE ACHIEVEMENT")
                        if isUpdate:
                            newArchived = {
                                'name': achievementData[0]['name'],
                                'level': []
                            }
                            newArchived['level'].append(newLevel)
                            accountCollection.update_one(
                                {"email": email},
                                {
                                    "$push": {
                                        'achievement': newArchived
                                    }
                                }
                            )
                        else:
                            accountCollection.update_one(
                                {
                                    "email": email,
                                    "achievement.name": achievementData[0]['name']
                                },
                                {
                                    "$push": {
                                        'achievement.$.level': newLevel
                                    }
                                }
                            )
                        newAchievement['levelUp'] = updateExp(expEarned, email)
                        newAchievement['message'] = "New Achievement Archived!"
                        newAchievement['status'] = "success"
                    else:
                        print("GA MASUK UPDATE ACHIEVEMENT")
                        newAchievement['levelUp'] = False
                        newAchievement['message'] = "No Achievement Archived!"
                        newAchievement['status'] = "error"
                else:
                    newAchievement['levelUp'] = False
                    newAchievement['message'] = "No Achievement Archived!"
                    newAchievement['status'] = "error"
            else:
                print("achievement 2")
                expEarned = 0
                newArchived = {
                    'name': achievementData[0]['name'],
                    'level': []
                }
                for achievement in achievementData[0]['level']:
                    if account[0]['level'] == achievement['requirements']['level']:
                        newArchived['level'].append({
                            "name": achievement['name'],
                            "description": achievement['description'],
                            "level": achievement['level'],
                            "createdAt": dateNow
                        })
                        expEarned = achievement['exp']
                        break
                
                accountCollection.update_one(
                    {"email": email},
                    {
                        "$push": {
                            'achievement': newArchived
                        }
                    }
                )
                newAchievement['levelUp'] = updateExp(expEarned, email)
                newAchievement['message'] = "New Achievement Archived!"
                newAchievement['status'] = "success"
        except Exception as e:
            print(e)
            print("achievement 11")
            newAchievement['message'] = "Internal Server Error!"
            newAchievement['status'] = "error"
    else:
        newAchievement['message'] = "Your account not found!"
        newAchievement['status'] = 'error'

    return newAchievement