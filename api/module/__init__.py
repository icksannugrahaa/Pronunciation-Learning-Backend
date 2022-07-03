from flask import Blueprint

module = Blueprint('module', __name__)

from . import main