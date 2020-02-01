# Neural Style Transfer - Flask
Implementation of a web app for neural style transfer using flask

## Description
This app uses [Flask](https://www.palletsprojects.com/p/flask/) as a web application framework together with [Celery](http://docs.celeryproject.org/en/latest/index.html) as an asynchronous task queue for long running processes.

[Supervisor](http://supervisord.org/) is also optionally used to run necessary processes in the background.

## Usage

### Environment Variables
Create a `.env` file with the following environment variables
```
CELERY_BROKER_URL=${YOUR_CELERY_BROKER_URL}
CELERY_RESULT_BACKEND=${YOUR_CELERY_RESULT_BACKEND_URL}
SECRET_KEY=${FLASK_SECRET_KEY}
```

### Running Celery
For a more detailed description of how to install Celery, please refer to the official Celery documentation [here](http://docs.celeryproject.org/en/latest/index.html). The [First Steps with Celery](http://docs.celeryproject.org/en/latest/getting-started/first-steps-with-celery.html) document provides steps on how to install the necessary components together with Celery basics.

I use RabbitMQ as a broker and Redis as a result backend. After installation, the broker runs in the background by default. You just have to start the redis server.

To disable the RabbitMQ service that starts up on boot:
```
$ sudo systemctl disable rabbitmq-server
```

If you need to run the RabbitMQ broker:
```
$ sudo rabbitmq-server
```

You can now run the Celery worker server:
```
$ celery -A tasks worker --loglevel=info
```

I used default values for the celery broker url (`pyamqp://`) and result backend (`redis://localhost:6379/0`). To set your own, just update the relevant values in the `.env` file.

### Running Flask
To run Flask:
```
$ export FLASK_APP=app.py
$ flask run
```

To make the server publicly available, simply add --host=0.0.0.0 to the command line:
```
$ flask run --host=0.0.0.0
```

### Using Supervisor to run Celery and Flask in the background
Run Supervisor with [`supervisord.conf`](supervisord.conf) as the config file:
```
$ sudo PATH=$PATH $BINDIR/supervisord -c ./supervisord.conf
```
`BINDIR` directory is the directory that your Python installation has been configured with. For example, for an installation of Python installed via `./configure --prefix=/usr/local/py; make; make install`, `BINDIR` would be `/usr/local/py/bin`. For more information about how to run Supervisor, you can refer to their [official documentation](http://supervisord.org/running.html).

`supervisorctl` can then be used as an interface to the features provided by supervisord.


#### Script to stop rabbitmq
For some reason unknown to me, Supervisor does not properly terminate the rabbitmq process when it tries to stop its child processes.

To solve this problem, a [script](scripts/rabbitmq.sh) is written to manually run `rabbitmqctl stop`.
