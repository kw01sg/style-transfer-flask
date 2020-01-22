import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import tensorflow as tf
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)
from werkzeug.utils import secure_filename

from src.model import VGG19Model
from src.utils import (get_white_noise_image, load_image, print_progress,
                       save_image)

# set logging level as tf.logging is removed in tf 2.0
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Content layer where we will pull our feature maps
CONTENT_LAYERS = ['block4_conv2']

# Style layer we are interested in
STYLE_LAYERS = ['block1_conv1',
                'block2_conv1',
                'block3_conv1',
                'block4_conv1',
                'block5_conv1']

# global variable so model is loaded before requests come in
style_content_model = VGG19Model(CONTENT_LAYERS, STYLE_LAYERS)

app = Flask(__name__)


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
            start_time = time.time()
            with NamedTemporaryFile(dir='./tmp') as content_file, NamedTemporaryFile(dir='./tmp') as style_file:
                content_image.save(content_file.name)
                style_image.save(style_file.name)
                output_file_path = get_output_image(
                    content_file.name, style_file.name, options)
            end_time = time.time()
            print("Total time: {:.1f}s".format(end_time-start_time))

            return render_template('result.html',
                                   output_path=output_file_path,
                                   total_time='{:.1f}s'.format(end_time-start_time))

        except Exception as error:
            print(error)

        return redirect(url_for('index'))


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


def get_output_image(content_path, style_path, options: dict):
    print('Running neural style transfer with the following parameters:')
    print()

    for key, value in options.items():
        print('\t{key}: {value}'.format(key=key, value=value))
    print()

    content_image, style_image = [load_image(
        path) for path in (content_path, style_path)]

    image = tf.Variable(get_white_noise_image(tf.shape(content_image)[1:])) \
        if options['white_noise_input'] else tf.Variable(content_image)

    style_targets = style_content_model(style_image)['style_outputs']
    content_targets = style_content_model(content_image)['content_outputs']

    opt = tf.keras.optimizers.Adam(
        learning_rate=options['learning_rate'], beta_1=0.99, epsilon=1e-1)

    style_content_model.compile(opt)

    for epoch in range(options['epochs']):
        epoch_start_time = time.time()
        for step in range(options['steps']):
            style_content_model.fit(image,
                                    content_targets=content_targets,
                                    style_targets=style_targets,
                                    content_layer_weights=[1],
                                    style_layer_weights=options['style_layer_weights'],
                                    content_weight=options['content_weight'],
                                    style_weight=options['style_weight'],
                                    variation_weight=options['variation_weight'])
            # printing in the loop as fit statement prints logs that causes epoch 0 statement to be separated from progress bar
            if step == 0:
                print('Epoch {epoch}/{epochs}'.format(
                    epoch=epoch+1, epochs=options['epochs']))

            print_progress(current_step=step+1, total_steps=options['steps'],
                           epoch_start_time=epoch_start_time)

    with NamedTemporaryFile(dir='./static/output') as output_file:
        save_image(image, Path(output_file.name + '.png'))

    return Path(output_file.name + '.png').name
