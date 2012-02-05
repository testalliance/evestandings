try:
    from flask import Flask
except ImportError:
    raise Exception('Flask is not available, please install if you wish to use Standings as a webapp')

from standings import Standings

app = Flask(__name__)
stdobj = Standings()

@app.route('/')
def standings():
    return stdobj._get_html()
