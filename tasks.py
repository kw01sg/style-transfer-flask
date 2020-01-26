import os
import time
from pathlib import Path

import tensorflow as tf
from celery import Celery

from src.model import VGG19Model
from src.utils import (get_white_noise_image, load_image, print_progress,
                       save_image)

# Content layer where we will pull our feature maps
CONTENT_LAYERS = ['block4_conv2']

# Style layer we are interested in
STYLE_LAYERS = ['block1_conv1',
                'block2_conv1',
                'block3_conv1',
                'block4_conv1',
                'block5_conv1']

celery = Celery(__name__,
                backend='redis://localhost:6379/0',
                broker='pyamqp://')


@celery.task(bind=True)
def get_output_image(self, content_path, style_path, options: dict):
    start_time = time.time()
    style_content_model = VGG19Model(CONTENT_LAYERS, STYLE_LAYERS)

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
        for step in range(options['steps']):
            style_content_model.fit(image,
                                    content_targets=content_targets,
                                    style_targets=style_targets,
                                    content_layer_weights=[1],
                                    style_layer_weights=options['style_layer_weights'],
                                    content_weight=options['content_weight'],
                                    style_weight=options['style_weight'],
                                    variation_weight=options['variation_weight'])
            self.update_state(state='PROGRESS',
                              meta={'current': options['steps'] * epoch + step,
                                    'total': options['steps'] * options['epochs'],
                                    'elapsed_time': "{:.1f}s".format(time.time() - start_time)})

    output_path = Path('./static/output') / (str(self.request.id) + '.png')
    save_image(image, Path(output_path))

    return {'output_path': str(output_path),
            'total_time': "{:.1f}s".format(time.time() - start_time)}


@celery.task
def clean_up_temp_images(content_path, style_path):
    os.remove(content_path)
    os.remove(style_path)


@celery.task
def add(x, y):
    print('in add')
    return x + y
