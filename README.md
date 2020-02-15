# Neural Style Transfer - Flask
Implementation of a web app for neural style transfer using flask

## Description
This app uses [Flask](https://www.palletsprojects.com/p/flask/) as a web application framework together with [Celery](http://docs.celeryproject.org/en/latest/index.html) as an asynchronous task queue for long running processes.

Docker and Docker-compose is used to run the application.

## Usage

### Environment Variables
Create a `.env` file with the following environment variables
```
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672
CELERY_RESULT_BACKEND=redis://redis:6379
SECRET_KEY=${FLASK_SECRET_KEY}
```

Celery Broker URL comes in the form:
```
amqp://myuser:mypassword@localhost:5672/myvhost
```
where `guest` and `guest` are used as defaults from the `rabbitmq` image. Update the `.env` file if required.

### Running
Because dependencies are setup using services, running the app is straight forward. The only complex option is running Tensorflow on GPU, as docker-compose does not support gpu option as of writing this readme.

This means that we cannot just use `docker-compose up` to run the app, but have to follow certain steps:

1. Start Redis and RabbitMQ
```
docker-compose up -d redis rabbitmq
```

2. Build Celery image
```
sudo docker-compose build celery
```

3. Start Celery on the same network as Redis and RabbitMQ
```
sudo docker run -d \
    --network=style-transfer-flask_default \
    --gpus all \
    --env-file .env \
    --rm \
    -v $PWD/tmp:/code/tmp \
    -v $PWD/static/output:/code/static/output \
    style-transfer-flask_celery \
    celery -A tasks worker -c 1 --loglevel=info
```
Remove the `--gpus all` option to run on CPU only.

4. Start Flask
```
docker-compose up -d web
```

Running the application for the first time will be slower since the pre-trained weights have to be downloaded.

To stop the application, use `docker stop` to stop the container running celery, and `docker-compose down` to stop the rest of the services.
