import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import tensorflow as tf
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)
from werkzeug.utils import secure_filename

from tasks import add, clean_up_temp_images, get_output_image

# set logging level as tf.logging is removed in tf 2.0
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
# app.config['CELERY_BROKER_URL'] = 'pyamqp://'
# app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/transform', methods=['GET', 'POST'])
def transform():
    if request.method == 'POST':
        # get files
        content_image = request.files['content_image']
        style_image = request.files['style_image']

        if content_image.filename == '' or style_image.filename == '':
            # flash('No selected files')
            return redirect(url_for('index'))

        if not allowed_file(content_image.filename) or not allowed_file(style_image.filename):
            return redirect(url_for('index'))

        try:
            options = get_options(request.form)
            print('Running neural style transfer with the following parameters:')
            print()

            for key, value in options.items():
                print('\t{key}: {value}'.format(key=key, value=value))
            print()

            with NamedTemporaryFile(dir='./tmp', delete=False) as content_file, \
                    NamedTemporaryFile(dir='./tmp', delete=False) as style_file:
                content_image.save(content_file.name)
                style_image.save(style_file.name)

            with app.app_context():
                task = get_output_image.apply_async(
                    (content_file.name,
                     style_file.name,
                     options), link=clean_up_temp_images.si(content_file.name,
                                                            style_file.name))

            return redirect(url_for('status', task_id=task.id))

        except Exception as error:
            print(error)

        return redirect(url_for('index'))


@app.route('/status/<task_id>', methods=['GET', 'POST'])
def status(task_id):
    if request.method == 'POST':
        task = get_output_image.AsyncResult(task_id)

        if task.state == 'SUCCESS':
            response = {
                'state': 'SUCCESS',
                'elapsed_time': task.result['total_time']
            }
            return jsonify(response)
        elif task.state != 'PENDING':
            response = {
                'state': task.state,
                'current': task.info['current'],
                'total': task.info['total'],
                'elapsed_time': task.info['elapsed_time']
            }
            return jsonify(response)
        else:
            return jsonify({'state': task.state})
    return render_template('status.html', task_id=task_id)


@app.route('/result/<task_id>')
def result(task_id):
    task = get_output_image.AsyncResult(task_id)
    result = task.result
    return render_template('result.html',
                           output_path=Path(result['output_path']).name,
                           total_time=result['total_time'])


def get_options(options):
    # TODO: validate inputs and throw exceptions if not validated
    result = dict(options)

    # convert to float
    for i in ['content_weight', 'style_weight', 'variation_weight', 'learning_rate']:
        result[i] = float(result[i])

    # convert to int
    for i in ['epochs', 'steps']:
        result[i] = int(result[i])

    # parse style layer weights
    result['style_layer_weights'] = [
        float(i) for i in result['style_layer_weights'].split()]

    # parse white noise input
    if 'white_noise_input' in result:
        result['white_noise_input'] = True
    else:
        result['white_noise_input'] = False

    return result
