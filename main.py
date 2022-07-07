from api import app
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

if __name__ == "__main__":
    app.run(host=os.environ.get('HOST') if os.environ.get('HOST') != '' else '0.0.0.0', 
            port=os.environ.get('PORT') if os.environ.get('PORT').isnumeric else 5000, 
            debug=os.environ.get('DEBUG') if os.environ.get('DEBUG') else True)