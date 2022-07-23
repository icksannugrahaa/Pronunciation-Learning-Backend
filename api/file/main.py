from api import app, db
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image
from . import file
from flask_cors import cross_origin
from flask import request, send_file, send_from_directory

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config["ALLOWED_IMAGE_EXTENSIONS"]

def uploadFile(request):
    results = {}
    responses = 500
    if request.method == 'POST':
        if 'file' not in request.files:
            results['message'] = "File not found!"
            results['status'] = False
            responses = 400
        else:
            file = request.files['file']
            mimetype = file.content_type
            filetype = mimetype.split('/')[0]
            if file.filename == '':
                results['message'] = "File not found!"
                results['status'] = False
                responses = 400
            else:
                if file and allowed_file(file.filename):
                    try:
                        fileUrl = ""
                        
                        # get file name
                        filename = secure_filename(file.filename)
                        filePath = request.form['path'] if 'path' in request.form else "images"
                        largeFileDir = os.path.join(app.config['UPLOAD_FOLDER']+"/"+filePath+"/lg")
                        smallFileDir = os.path.join(app.config['UPLOAD_FOLDER']+"/"+filePath+"/sm")
                        mediumFileDir = os.path.join(app.config['UPLOAD_FOLDER']+"/"+filePath+"/md")
                        originalFileDir = os.path.join(app.config['UPLOAD_FOLDER']+"/"+filePath+"/original")

                        # check dir, if not exist make a dir
                        if not os.path.exists(largeFileDir):
                            os.makedirs(largeFileDir)
                        if not os.path.exists(smallFileDir):
                            os.makedirs(smallFileDir)
                        if not os.path.exists(mediumFileDir):
                            os.makedirs(mediumFileDir)
                        if not os.path.exists(originalFileDir):
                            os.makedirs(originalFileDir)
                        
                        # save file
                        fileUrl = os.path.join(originalFileDir, filename)
                        file.save(fileUrl)
                        
                        if filetype == 'audio' :
                            results['view'] = app.config['API_BASE_URL']+"/api/file/show?filename="+filename+"&path=/"+filePath
                            results['download'] = app.config['API_BASE_URL']+"/api/file/download?filename="+filename+"&path=/"+filePath
                        elif filetype == 'image':
                           
                            #resize image
                            openImage = Image.open(os.path.join(originalFileDir, filename))
                            
                            sm = openImage.resize((160,160),Image.ANTIALIAS)
                            md = openImage.resize((540,540),Image.ANTIALIAS)
                            lg = openImage.resize((1080,1080),Image.ANTIALIAS)
                            imageSMUrl = os.path.join(smallFileDir, filename)
                            imageMDUrl = os.path.join(mediumFileDir, filename)
                            imageLGUrl = os.path.join(largeFileDir, filename)
                            
                            sm.save(imageSMUrl,optimize=True,quality=95)
                            md.save(imageMDUrl,optimize=True,quality=95)
                            lg.save(imageLGUrl,optimize=True,quality=95)

                            # rename image
                            renameImage = uuid.uuid4()
                            fileType = filename.split('.')
                            newImageName = str(renameImage)+"."+fileType[len(fileType)-1]
                            os.rename(fileUrl, os.path.join(originalFileDir, newImageName))
                            os.rename(imageSMUrl, os.path.join(smallFileDir, newImageName))
                            os.rename(imageMDUrl, os.path.join(mediumFileDir, newImageName))
                            os.rename(imageLGUrl, os.path.join(largeFileDir, newImageName))
                            results['view'] = app.config['API_BASE_URL']+"/api/file/show?filename="+newImageName+"&path=/"+filePath
                            results['download'] = app.config['API_BASE_URL']+"/api/file/download?filename="+newImageName+"&path=/"+filePath
                            

                        # return
                        results['status'] = True
                        results['message'] = "Upload success !"
                        responses = 200
                    except Exception as e:
                        print(e)
                        results['message'] = "Internal Server Error!"
                        results['status'] = 'error'
                        responses = 500
                else:
                    results['status'] = "error"
                    results['message'] = "Your file is cant uploaded, please upload image only !"
                    responses = 403
    else:
        results['message'] = "Method Not Alowed"
        results['status'] = 'error'
        responses = 405

    return [results, responses]

@file.route('/upload', methods=['POST'])
@cross_origin()
def start():
    results = {}
    responses = 500
    upload = uploadFile(request)
    results = upload[0]
    responses = upload[1]

    return results, responses

@file.route('show', methods=['GET'])
@cross_origin()
def displayImage():
    results = {}
    responses = 500
    results['status'] = "error"
    results['message'] = "Error Server !"
    if 'filename' in request.args and 'path' in request.args:
        filename = request.args['filename']
        expath = request.args['path']
        type = request.args['type'] if 'type' in request.args else 'original'
        file_path = os.path.join(app.config["UPLOAD_FOLDER"]+expath+"/"+type, filename)
        print(file_path)
        if os.path.isfile(file_path):
            return send_file(file_path)
        else:
            results['status'] = "error"
            results['message'] = "File not found !"
            responses = 403
    else:
        results['status'] = "error"
        results['message'] = "Periksa kembali form input !"
        responses = 400

    return results, responses


@file.route('download', methods=['GET'])
@cross_origin()
def download():
    results = {}
    responses = 500
    results['status'] = "error"
    results['message'] = "Error Server !"
    if 'filename' in request.args and 'path' in request.args:
        filename = request.args['filename']
        expath = request.args['path']
        type = request.args['type'] if 'type' in request.args else 'original'
        path = app.config["UPLOAD_FOLDER"]+expath+"/"+type
        file_path = os.path.join(path, filename)
        if os.path.isfile(file_path):
            return send_from_directory(path, filename, as_attachment=True)
        else:
            results['status'] = "error"
            results['message'] = "File not found !"
    else:
        results['status'] = "error"
        results['message'] = "Periksa kembali form input !"
        responses = 400

    return results, responses
