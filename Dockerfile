# FROM apache/airflow:2.0.1

# COPY requirements.txt /requirements.txt
# RUN pip install --user --upgrade pip
# RUN pip install --no-cache-dir --user -r /requirements.txt

FROM apache/airflow:latest

USER root
RUN apt-get update && \
    apt-get -y install git && \
    apt-get clean

USER airflow

RUN pip install --no-cache-dir selenium
RUN pip install --no-cache-dir pandas
RUN pip install --no-cache-dir PyPDF2