#
# Flask Hello World
#
from flask import Flask
app = Flask(__name__)


@app.route('/')
def hello_world():
    return '<iframe src="https://plot.ly/~yves/1041/tick-data-stream/" width="750px" height="550px"></iframe>'


if __name__ == '__main__':
    app.run(port=9999, debug=True)