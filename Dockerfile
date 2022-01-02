FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN mkdir /data

COPY 'covid_data_getter.py' .

CMD [ "python3", "covid_data_getter.py", "--csvdir", "/data" ]
