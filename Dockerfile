# Load docker image with Java
FROM python:3.8-bookworm
# RUN apk add --no-cache python3-dev openssl-dev libffi-dev libc-dev gcc g++ jpeg-dev zlib-dev libjpeg make libsodium-dev musl-dev linux-headers && pip3 install --upgrade pip
RUN apt-get update
RUN apt-get install -y python3-dev libssl-dev libffi-dev libc-dev gcc g++ libjpeg-dev zlib1g-dev make libsodium-dev musl-dev && pip3 install --upgrade pip
# RUN apk --no-cache add musl-dev linux-headers g++
# RUN apk-install python3-dev libffi-dev
# Copy source files to image
COPY requirements.txt /home/python/requirements.txt
# Copy resource files needed for execution
WORKDIR /home/python
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install -r requirements.txt
# COPY src /home/python/src
COPY cs4545 /home/python/cs4545
COPY topologies /home/python/topologies
CMD python -u -m cs4545.system.run $PID $TOPOLOGY $ALGORITHM -location=$LOCATION -docker
