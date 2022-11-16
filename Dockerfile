# Load docker image with Java
FROM python:3.8-alpine
# Copy source files to image
COPY src /home/python/src
COPY requirements.txt /home/python/requirements.txt
# Copy resource files needed for execution
COPY resources/addresses_docker.txt /home/python/resources/addresses.txt
WORKDIR /home/python
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install -r requirements.txt
CMD python -u src/main.py $PID
