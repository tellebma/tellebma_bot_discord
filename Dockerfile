FROM python:3.9-slim
LABEL maintainer="tellebma"

RUN apt-get update && apt-get install -y locales \
    && echo "fr_FR.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen fr_FR.UTF-8

ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR:fr
ENV LC_ALL fr_FR.UTF-8

COPY . /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
