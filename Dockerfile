# Load docker image with Java
FROM python:3.8-alpine
# Copy source files to image
COPY src /home/python/src
# Copy resource files needed for execution
COPY resources/addresses_docker.txt /home/python/resources/addresses.txt
WORKDIR /home/python
CMD python -u src/main.py $PID
