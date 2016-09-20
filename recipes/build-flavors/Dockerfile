FROM artbio/ansible-galaxy-os
MAINTAINER Marius van den Beek, m.vandenbeek@gmail.com

RUN apt-get update && apt-get install -y libxml2-dev libxslt1-dev && \
    git clone --recursive -b stable-2.1 https://github.com/ansible/ansible && \
    pip install ansible/ && pip install --upgrade ifbcloud bioblend nose setuptools mock && \
    git clone https://github.com/galaxyproject/bioblend.git

ADD build.sh /build.sh
RUN chmod +x /build.sh

CMD /build.sh
