# Load docker image with Java
FROM python:3.8-alpine
RUN apk add --no-cache python3-dev openssl-dev libffi-dev libc-dev gcc libsodium && pip3 install --upgrade pip
# RUN apk-install python3-dev libffi-dev
# Copy source files to image
COPY requirements.txt /home/python/requirements.txt
# Copy resource files needed for execution
WORKDIR /home/python
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install -r requirements.txt
COPY src /home/python/src
COPY topologies /home/python/topologies
CMD python -u src/run.py $PID $TOPOLOGY $ALGORITHM -docker
