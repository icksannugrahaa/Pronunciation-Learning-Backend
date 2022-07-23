from flask import Blueprint

predict = Blueprint('predict', __name__)

from . import main