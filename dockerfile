FROM python:3.6-slim
RUN apt-get update && apt-get install -y vim
WORKDIR /code
ENV FLASK_APP app.py
COPY . .
# Requires the latest pip for tensorflow 2
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
CMD ["flask", "run", "--host=0.0.0.0"]
