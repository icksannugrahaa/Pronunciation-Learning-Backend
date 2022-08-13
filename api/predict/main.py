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
    try:
        
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
                print(checkFinalString[len(checkFinalString)-2])
                print(str2rm[i-1])
                if str2rm[i-1] != "" and checkFinalString[len(checkFinalString)-2] != "" and checkFinalString[len(checkFinalString)-2] != str2rm[i-1]:
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
            "totalScore": round(totalScore, 1),
            "finalText": finalString,
            "wrong": wrongAnswer,
            "wrongScore": round(wrongScoreFinal, 1),
            "outWord": wordOut,
            "outWordScore": round(wordOutScoreFinal, 1),
            "right": rightAnswer,
            "rightScore": round(rightScoreFinal, 1)
        }
    except Exception as e:
        print(str(e))
        return {
            "error": str(e)
        }

def audio_duration(length):
    hours = length // 3600  # calculate in hours
    length %= 3600
    mins = length // 60  # calculate in minutes
    length %= 60
    seconds = length  # calculate in seconds
  
    return hours, mins, seconds  # returns the duration

def text_to_speech(text, filename):
    results = {}
    newPath = os.path.join(
        app.config["UPLOAD_FOLDER"]+"/others/original", filename)
    print(filename)
    print(newPath)
    # SSML CONFIG
    voicName = 'en-US-JennyNeural'
    speakingRate = '-40%'
    pitch = 'high'
    voiceStyle = 'cheerful'
    languageCode = 'en-US'
    
    if text == "" or text is None:
        text = "You don't speak anything!"
    
    head1 = f'<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="{languageCode}">'
    head2 = f'<voice name="{voicName}">'
    head3 =f'<mstts:express-as style="{voiceStyle}">'
    head4 = f'<prosody rate="{speakingRate}" pitch="{pitch}">'
    tail= '</prosody></mstts:express-as></voice></speak>'

    ssml = head1 + head2 + head3 + head4 + text + tail
    
    #SPEECH CONFIG
    speech_config = speechsdk.SpeechConfig(subscription=os.environ.get(
        'SPEECH_SUBSCRIPTION'), region=os.environ.get('SPEECH_REGION'))
    audio_config = speechsdk.audio.AudioOutputConfig(filename=newPath)

    #GET RESULT
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    speech_synthesis_result = speech_synthesizer.speak_ssml_async(ssml).get()

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        results['status'] = "success"
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        results['status'] = "error"
        results['error'] = str(cancellation_details.error_details)
    return results

def recognition_from_file(filename, path):
    results = {}
    newPath = os.path.join(
        app.config["UPLOAD_FOLDER"]+"/"+path+"/original", filename)
    print(filename)
    print(newPath)
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

@predict.route('/tts', methods=['POST'])
@jwt_required()
@cross_origin()
def tts():
    results = {}
    response = 500
    if request.method == 'POST':
        currentAccount = get_jwt_identity()
        account = list(accountCollection.find({'email': currentAccount}))
        if len(account) > 0:
            print(request.form)
            if 'text' not in request.form and 'filename' not in request.form:
                results['message'] = "Request not valid!"
                results['status'] = 'error'
                response = 400
            else:
                try:
                    resTTS = text_to_speech(request.form['text'], request.form['filename'])
                    if resTTS['status'] == "success":
                        results['view'] = "api/file/show?filename="+request.form['filename']+"&path=/others"
                        results['message'] = "Speech synthesized!"
                        results['status'] = 'success'
                        response = 200
                    else:
                        results['message'] = "Speech failed synthesized!"
                        results['status'] = 'error'
                        results['error'] = str(resTTS['error'])
                        response = 200
                except Exception as e:
                    print(e)
                    results['error'] = str(e)
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
                try :
                    file = request.files['file']
                    filename = file.filename
                    filenameSplit = filename.split('-')
                    username = ' '.join(filenameSplit[0].split('_'))
                    if username == account[0]['name']:
                        lessonOrder = int(filenameSplit[4].split(".")[0])
                        lessonType = 'theory'
                        lessonTypes = 'question'
                        query = {
                            "order": int(filenameSplit[1]),
                            "lessons.order": int(filenameSplit[2]),
                        }
                        if filenameSplit[3] == "t":
                            query['lessons.theory.order'] = lessonOrder
                            lessonType = 'theory'
                            lessonTypes = 'question'
                        elif filenameSplit[3] == "q":
                            query['lessons.quiz.order'] = lessonOrder
                            lessonType = 'quiz'
                            lessonTypes = 'answer'
                        lessonData = list(moduleCollection.find(query))
                        lessonQuest = lessonData[0]['lessons'][int(filenameSplit[2])-1][lessonType][lessonOrder-1][lessonTypes]
                        if len(lessonData) > 0:
                            upload = uploadFile(request)
                            results = upload[0]
                            print(results)
                            if results['status'] == True:
                                filePath = request.form['path'] if 'path' in request.form else "others"
                                filenameJoin = '_'.join(filenameSplit[0].split(' '))
                                newFileName = filenameJoin+"-"+filenameSplit[1]+"-"+filenameSplit[2]+"-"+filenameSplit[3]+"-"+filenameSplit[4]
                                print(newFileName)
                                resSpeech = recognition_from_file(newFileName, filePath)
                                print(resSpeech)
                                if resSpeech['status'] == "success":
                                    audio = WAVE(os.path.join(app.config["UPLOAD_FOLDER"]+"/"+filePath+"/original", newFileName))
                                    audio_info = audio.info
                                    length = int(audio_info.length)
                                    hours, mins, seconds = audio_duration(length)
                                    level = "beginner"
                                    if lessonData[0]['level'] >= 1 and lessonData[0]['level'] <= 5:
                                        level = "beginner"
                                    elif lessonData[0]['level'] >= 6 and lessonData[0]['level'] <= 10:
                                        level = "intermediate"
                                    
                                    print(lessonQuest)
                                    print(filenameSplit[3])
                                    if filenameSplit[3] == "t":
                                        resScore = count_score(lessonQuest, resSpeech['text'], seconds, level)
                                        resScore['textPredict'] = resSpeech['text']
                                        resScore['textQuest'] = lessonQuest
                                        resScore['view'] = results['view']
                                        resScore['download'] = results['download']
                                        results['data'] = resScore
                                        results['message'] = "Process Success!"
                                        results['status'] = "success"
                                    elif filenameSplit[3] == "q":
                                        highScoreIndex = 0
                                        highScore = 0
                                        resScoreFinal = []
                                        for ianswer, answer in enumerate(lessonQuest):
                                            print(ianswer)
                                            print(answer)
                                            resScore = count_score(answer, resSpeech['text'], seconds, level)
                                            if len(resScore) < 8: 
                                                continue
                                            elif resScore['totalScore'] > highScore:
                                                highScore = resScore['totalScore']
                                                highScoreIndex = ianswer
                                                resScoreFinal = resScore
                                        # print(highScore)
                                        # print(resScoreFinal)
                                        resScoreFinal['textPredict'] = resSpeech['text']
                                        resScoreFinal['textPredict'] = resSpeech['text']
                                        resScoreFinal['textQuest'] = lessonQuest[highScoreIndex]
                                        resScoreFinal['view'] = results['view']
                                        resScoreFinal['download'] = results['download']
                                        results['data'] = resScoreFinal
                                        results['message'] = "Process Success!"
                                        results['status'] = "success"
                                    
                                    results.pop('view', None)
                                    results.pop('download', None)
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
                except Exception as e:
                    print(e)
                    results['error'] = str(e)
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
