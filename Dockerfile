FROM jenkins
# if we want to install via apt
USER root
RUN apt-get update && apt-get install -y ruby make python-virtualenv \
    apt-transport-https software-properties-common
RUN apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
RUN echo "deb https://apt.dockerproject.org/repo debian-jessie main" > /etc/apt/sources.list.d/docker.list
RUN apt-get update && apt-get install -y docker-engine
RUN adduser jenkins docker
COPY plugins.txt /usr/share/jenkins/plugins.txt
RUN /usr/local/bin/plugins.sh /usr/share/jenkins/plugins.txt
# drop back to the regular jenkins user - good practice
USER jenkins
