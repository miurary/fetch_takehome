FROM python:3.9

WORKDIR /fetch_takehome

COPY . .

RUN pip3 install -r requirements.txt

EXPOSE 5000

CMD ["python3", "fetch_takehome.py"]