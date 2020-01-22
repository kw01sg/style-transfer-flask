from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/transform', methods=['GET', 'POST'])
def transform():
    if request.method == 'POST':
        return jsonify(request.form)
