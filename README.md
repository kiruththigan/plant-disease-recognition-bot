# Automated Plant Disease Recognition System Bot

pip3 install -r requirements.txt

python3 main.py


# Docker Image

docker build . -t plant-care-bot

docker images

docker run -p 8001:8001 --env-file .env plant-care-bot