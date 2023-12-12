FROM python:3.10-slim-bullseye
#RUN echo "deb http://security.debian.org/debian-security bullseye-security main contrib non-free\ndeb http://httpredir.debian.org/debian jessie main contrib\ndeb-src http://httpredir.debian.org/debian jessie main contrib\ndeb http://httpredir.debian.org/debian jessie-updates main contrib\ndeb-src http://httpredir.debian.org/debian jessie-updates main contrib\ndeb http://security.debian.org/ jessie/updates main contrib\ndeb-src http://security.debian.org/ jessie/updates main contrib " >> /etc/apt/sources.list


#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 112695A0E562B32A
#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 54404762BBB6E853

RUN apt-get update

RUN git config --global user.name "noor.raghib.12"
RUN git config --global user.email "noor.raghib.12@gmail.com"

# Make ssh dir
RUN mkdir /root/.ssh/

# Copy over private key, and set permissions
# Warning! Anyone who gets their hands on this image will be able
# to retrieve this private key file from the corresponding image layer
COPY /home/mehedi/.ssh/id_rsa /root/.ssh/id_rsa

RUN chmod 600 /root/.ssh/id_rsa

# Create known_hosts
# Add gitlab key
RUN eval $(ssh-agent -s) && \
    ssh-add /root/.ssh/id_rsa && \
    ssh-keyscan gitlab.com >> /root/.ssh/known_hosts


WORKDIR /usr/src/app
RUN git clone git@gitlab.com:swt-webgeeks-ml-ai/grey-birthdayllm.git

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get install -y libtiff5-dev libjpeg8-dev libopenjp2-7-dev zlib1g-dev \
    libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python3-tk \
    libharfbuzz-dev libfribidi-dev libxcb1-dev python3-dev python3-setuptools \ 
    libevent-dev build-essential libpq-dev git python3-pip

RUN pip install -U pip flask langchain chromadb

EXPOSE 5000
