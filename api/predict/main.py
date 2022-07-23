from flask import request
from api import db, app
from . import predict
from api.file.main import uploadFile
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv, find_dotenv
import math
import mutagen
from mutagen.wave import WAVE

accountCollection = db.accounts
moduleCollection = db.modules

load_dotenv(find_dotenv())

def count_score(str1, str2, time, level):
    str1 = str1.lower()
    str2 = str2.lower()
    totalCharacters = len(str1.split(" "))
    rightAnswer = 0
    wrongAnswer = 0
    finalString = ""
    wordOut = 0

    #penentuan bobot kelasahan
    totalScore = 100
    if level == "beginner": # benar 100% - salah 90%
        wordOutScore = (0.2*totalCharacters) # 20% dari kesalahan
        timeScore = (0.3*totalCharacters)# 30% dari kesalahan
        timeScore = math.floor(timeScore * round(time/totalCharacters)) # waktu di bulatkan ke nilai terkecil
        wrongScore = (0.4*totalCharacters) # 40% dari kesalahan
        rightScore = totalCharacters # 100% dari nilai benar
    elif level == "intermediate":  # benar 100% - salah 100%
        wordOutScore = round(0.2*totalCharacters) # 20% dari kesalahan
        timeScore = round(0.3*totalCharacters) # 30% dari kesalahan
        timeScore = timeScore * round(time/(totalCharacters/2)) # waktu di bulatkan
        wrongScore = round(0.5*totalCharacters) # 50% dari kesalahan
        rightScore = totalCharacters
    elif level == "advanced": # benar 100% - salah 110%
        wordOutScore = round(0.2*totalCharacters) # 20% dari kesalahan
        timeScore = round(0.4*totalCharacters) # 40% dari kesalahan
        timeScore = timeScore * round(time/(totalCharacters/3))
        wrongScore = round(0.5*totalCharacters) # 50% dari kesalahan
        rightScore = totalCharacters
        
    # Remove special characters
    str1rm = ''
    str2rm = ''
    for data in str1.split(' '):
        str1rm += ''.join(char for char in data if char.isalnum())
        str1rm += ' '
    for data in str2.split(' '): 
        str2rm += ''.join(char for char in data if char.isalnum())
        str2rm += ' '

    # Compare String
    readUntil = 3
    str1rm = str1rm.split(' ')
    str2rm = str2rm.split(' ')
    loopingIndex = len(str1rm) if len(str1rm) > len(str2rm) else len(str2rm)

    for i in range(loopingIndex):
        # print(i)
        if i < len(str1rm) and i < len(str2rm):
            if str1rm[i] != "" and str2rm[i] != "":
                if str1rm[i] == str2rm[i]:
                    finalString += str2rm[i]+" "
                    rightAnswer += 1
                else:
                    for j in range(readUntil):
                        if (j+i) < len(str1rm) and (j+i) < len(str2rm):
                            if str1rm[i] == str2rm[i+j]:
                                checkFinalString = finalString.split(" ")
                                if checkFinalString[len(checkFinalString)-2] != str2rm[i]:
                                    finalString += "<" + str2rm[i]+"> "
                                    wordOut += 1
                                finalString += str2rm[i+j]+" "
                                rightAnswer += 1
                                break
                            else:
                                if (j+1) == readUntil:
                                    checkFinalString = finalString.split(" ")
                                    if checkFinalString[len(checkFinalString)-2] != "<"+str2rm[i]+">":
                                        finalString += "<" + str2rm[i] + "> "
                                        wordOut += 1
                                        break
                                    else:
                                        continue
                                else:
                                    continue
                        else:
                            checkFinalString = finalString.split(" ")
                            
                            if checkFinalString[len(checkFinalString)-2] != "<"+str2rm[i]+">":
                                finalString += "<" + str2rm[i] + "> "
                                wordOut += 1
                            else:
                                finalString += str2rm[i] + " "
                                rightAnswer += 1
                                break
        else:
            checkFinalString = finalString.split(" ")
            if str2rm[i-1] != "" and checkFinalString[len(checkFinalString)-1] != str2rm[i-1]:
                finalString += "<" + str2rm[i-1] + "> "
                wordOut += 1
        
                
    # menghitung nilai sementara
    wrongAnswer = (totalCharacters - rightAnswer)
    wordOut = (wordOut - wrongAnswer)

    # menghitung nilai akhir
    wrongScoreFinal = ((wrongAnswer/wrongScore)) if wrongAnswer > 0 else 0
    rightScoreFinal = ((rightAnswer/rightScore)*100) if rightAnswer > 0 else 0
    wordOutScoreFinal = ((wordOut/wordOutScore)) if wordOut > 0 else 0
    totalScore = (((rightScoreFinal - timeScore) - wrongScoreFinal) - wordOutScoreFinal)
    
    return {
        "totalScore": totalScore,
        "finalText": finalString,
        "wrong": wrongAnswer,
        "wrongScore": wrongScoreFinal,
        "outWord": wordOut,
        "outWordScore": wordOutScoreFinal,
        "right": rightAnswer,
        "rightScore": rightScoreFinal
    }

def audio_duration(length):
    hours = length // 3600  # calculate in hours
    length %= 3600
    mins = length // 60  # calculate in minutes
    length %= 60
    seconds = length  # calculate in seconds
  
    return hours, mins, seconds  # returns the duration

def from_file(filename, path):
    results = {}
    newPath = os.path.join(
        app.config["UPLOAD_FOLDER"]+"/"+path+"/original", filename)
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get(
        'SPEECH_SUBSCRIPTION'), region=os.environ.get('SPEECH_REGION'))
    audio_input = speechsdk.AudioConfig(filename=newPath)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_input)

    result = speech_recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        results['text'] = result.text
        results['status'] = "success"
        print("Recognized: {}".format(result.text))
    elif result.reason == speechsdk.ResultReason.NoMatch:
        results['status'] = "error"
        results['error'] = "No speech could be recognized: {}".format(result.no_match_details)
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        results['status'] = "error"
        results['error'] = "Speech Recognition canceled: {}".format(cancellation_details.error_details)
    return results


@predict.route('/get', methods=['POST'])
@jwt_required()
@cross_origin()
def index():
    results = {}
    response = 500
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        if len(account) > 0:
            if 'file' not in request.files:
                results['message'] = "File not found!"
                results['status'] = False
                response = 400
            else:
                file = request.files['file']
                filename = file.filename
                filenameSplit = filename.split('-')
                username = ' '.join(filenameSplit[0].split('_'))
                if username == account[0]['name']:
                    lessonOrder = int(filenameSplit[4].split(".")[0])
                    query = {
                        "order": int(filenameSplit[1]),
                        "lessons.order": int(filenameSplit[2]),
                    }
                    if filenameSplit[3] == "t":
                        query['lessons.theory.order'] = lessonOrder
                    elif filenameSplit[3] == "q":
                        query['lessons.quiz.order'] = lessonOrder
                    lessonData = list(moduleCollection.find(query))
                    lessonQuest = lessonData[0]['lessons'][int(filenameSplit[2])-1]['theory'][lessonOrder-1]['question']
                    
                    if len(lessonData) > 0:
                        upload = uploadFile(request)
                        results = upload[0]
                        if results['status'] == True:
                            filePath = request.form['path'] if 'path' in request.form else "others"
                            resSpeech = from_file(filename, filePath)
                            if resSpeech['status'] == "success":
                                audio = WAVE(os.path.join(app.config["UPLOAD_FOLDER"]+"/"+filePath+"/original", filename))
                                audio_info = audio.info
                                length = int(audio_info.length)
                                hours, mins, seconds = audio_duration(length)
                                level = "beginner"
                                if lessonData[0]['level'] >= 1 and lessonData[0]['level'] <= 5:
                                    level = "beginner"
                                elif lessonData[0]['level'] >= 6 and lessonData[0]['level'] <= 10:
                                    level = "intermediate"
                                    
                                if filenameSplit[3] == "t":
                                    resScore = count_score(lessonQuest, resSpeech['text'], seconds, level)
                                    resScore['textPredict'] = resSpeech['text']
                                    resScore['textQuest'] = lessonQuest
                                    results['data'] = resScore
                                    results['message'] = "Process Success!"
                                    results['status'] = "success"
                                elif filenameSplit[3] == "q":
                                    resScore = count_score(lessonQuest, resSpeech['text'], seconds, level)
                                    resScore['textPredict'] = resSpeech['text']
                                    results['data'] = resScore
                                    results['message'] = "Process Success!"
                                    results['status'] = "success"
                            else:
                                results['message'] = "Predict failed!"
                                results['status'] = "error"
                        else:
                            results['message'] = "File upload failed!"
                            results['status'] = "error"
                    else:
                        results['message'] = "Lesson not found!"
                        results['status'] = "error"
                else:
                    results['message'] = "Your account get an exception!"
                    results['status'] = "error"
                response = 200
        else:
            results['message'] = "Your account not found!"
            results['status'] = 'error'
            response = 403
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = "error"
        response = 405

    return results, response
