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
                                progressType = progressItem['progress'].split("-")[0]
                                if progressType == "t" and progressItem['status'] == "done":
                                    progressDone += 1
                            print("achievement 12")   
                            
                    # find achievement
                    achievementData = list(achievementCollection.find({'name': "Theory Achievement"}).limit(1))
                    
                    print("achievement 13")
                    
                    # check user achievement
                    if len(account[0]['achievement']) > 0:
                        print("achievement 1")
                        newLevel = {}
                        expEarned = 0
                        for userAchievement in account[0]['achievement']:
                            for achievement in achievementData[0]['level']:
                                if userAchievement['name'] == achievementData[0]['name']:
                                    for userAchievementLevel in userAchievement['level']:
                                        if progressDone == achievement['requirements']['theory']:
                                            if  achievement['level'] >= userAchievementLevel['level']:
                                                newLevel = {
                                                    "name": achievement['name'],
                                                    "description": achievement['description'],
                                                    "level": achievement['level'],
                                                    "createdAt": dateNow
                                                }
                                                expEarned = achievement['exp']
                        if newLevel is not None and len(newLevel) > 0:
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
                            if progressDone == achievement['requirements']['theory']:
                                newArchived['level'].append({
                                    "name": achievement['name'],
                                    "description": achievement['description'],
                                    "level": achievement['level'],
                                    "createdAt": dateNow
                                })
                                expEarned = achievement['exp']
                        
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
            print("quizz 3")
            if len(progressData) > 0:
                print("quizz 4")
                if len(progressData[0]['allProgress']) > 0:
                    print("quizz 5")
                    #init data
                    progressDone = 0
                    newArchived = {}
                    dateNow = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    for progress in progressData[0]['allProgress']:
                        print("quizz 6")
                        if len(progress['progress']) > 0:
                            print("quizz 7")
                            # check progress
                            for progressItem in progress['progress']:
                                progressType = progressItem['progress'].split("-")[0]
                                if progressType == "q" and progressItem['status'] == "done":
                                    progressDone += 1
                            print("quizz 12")
                            
                    # find achievement
                    achievementData = list(achievementCollection.find({'name': "Quizz Achievement"}).limit(1))
                    
                    print("quizz 13")
                    
                    # check user achievement
                    if len(account[0]['achievement']) > 0:
                        print("quizz 1")
                        newLevel = {}
                        newArchived = {
                            'name': achievementData[0]['name'],
                            'level': []
                        }
                        expEarned = 0
                        for userAchievement in account[0]['achievement']:
                            for achievement in achievementData[0]['level']:
                                if userAchievement['name'] == achievementData[0]['name']:
                                    for userAchievementLevel in userAchievement['level']:
                                        if progressDone == achievement['requirements']['quizz']:
                                            if  achievement['level'] >= userAchievementLevel['level']:
                                                newLevel = {
                                                    "name": achievement['name'],
                                                    "description": achievement['description'],
                                                    "level": achievement['level'],
                                                    "createdAt": dateNow
                                                }
                                                expEarned = achievement['exp']
                                else:
                                    if progressDone == achievement['requirements']['quizz']:
                                        newArchived['level'].append({
                                            "name": achievement['name'],
                                            "description": achievement['description'],
                                            "level": achievement['level'],
                                            "createdAt": dateNow
                                        })
                                        expEarned = achievement['exp']
                        print("quizz 1.1")
                        if newLevel is not None and len(newLevel) > 0:
                            print("quizz 1.2")
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
                        elif newArchived is not None and len(newArchived['level']) > 0:
                            print("quizz 1.3")
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
                            print("quizz 1.4")
                            newAchievement['levelUp'] = False
                            newAchievement['message'] = "No Achievement Archived!"
                            newAchievement['status'] = "error"
                    else:
                        print("quizz 2")
                        print(achievementData)
                        newArchived = {
                            'name': achievementData[0]['name'],
                            'level': []
                        }
                        expEarned = 0
                        for achievement in achievementData[0]['level']:
                            if progressDone == achievement['requirements']['quizz']:
                                newArchived['level'].append({
                                    "name": achievement['name'],
                                    "description": achievement['description'],
                                    "level": achievement['level'],
                                    "createdAt": dateNow
                                })
                                expEarned = achievement['exp']
                        
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
                    print("quizz 9")
                    newAchievement['message'] = "No Achievement Archived!"
                    newAchievement['status'] = "error"
            else:
                print("quizz 10")
                newAchievement['message'] = "No Achievement Archived!"
                newAchievement['status'] = "error"
        except Exception as e:
            print(e)
            print("quizz 11")
            newAchievement['message'] = "Internal Server Error!"
            newAchievement['status'] = "error"
    else:
        newAchievement['message'] = "Your account not found!"
        newAchievement['status'] = 'error'

    return newAchievement