# docker build -t xml-parser-api .
# docker run -d --name xml_parser_api -p 8000:8000 xml-parser-api

FROM python:3.10

# set the working directory
WORKDIR /xml_parser_app

# install dependencies
COPY ./requirements.txt /xml_parser_app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the scripts to the folder
COPY . /xml_parser_app

# start the server
CMD ["uvicorn", "main:xml_parser_app", "--host", "0.0.0.0", "--port", "8000"]