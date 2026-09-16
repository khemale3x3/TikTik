FROM mcr.microsoft.com/playwright:focal

RUN apt-get update && apt-get install -y python3-pip

WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .
RUN pip3 install .
RUN python3 -m playwright install

CMD ["python3"]
