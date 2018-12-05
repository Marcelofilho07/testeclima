import os
import json
import traceback
import requests

from cities_list import CITIES
from flask import Flask, request

token = os.environ.get('FB_ACCESS_TOKEN') #FB_ACCESS_TOKEN é definida no Heroku
api_key = os.environ.get('WEATHER_API_KEY') #WHEATER_API_KEY é definida no Heroku
app = Flask(__name__)

#Essa função envia ao usuário a solicitação da localização do mesmo
def location_quick_reply(sender):
    return { "recipient": { "id": sender},"message": {"text": "Compartilhe sua localização:","quick_replies": [{"content_type": "location",}]}}

#Essa função envia ao usuário uma mensagem
def send_message(payload):
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)

#Essa função envia as informações sobre o clima para o usuário
def send_weather_info(sender, **kwargs):
    latitude = kwargs.pop('latitude', None)
    longitude = kwargs.pop('longitude', None)
    city_name = kwargs.pop('city_name', None)

    #Checa se o query de busca sera por latitude e longitude ou pelo nome da cidade
    if latitude and longitude:
        query = 'lat={}&lon={}'.format(latitude, longitude)
    elif city_name:
        query = 'q={},br'.format(city_name)

    #URL que disponibiliza o json com informações sobre o clima
    url = 'http://api.openweathermap.org/data/2.5/weather?' \
          '{}&appid={}&units={}&lang={}'.format(query,api_key,'metric','pt')

    r = requests.get(url)
    response = r.json()

    if 'cod' in response:
        if response['cod'] != 200:
            return 'error'

    #Alocando informações do clima em variáveis e enviando para o usuário
    description = r.json()['weather'][0]['description'].title()
    weather = r.json()['main']
    wind = r.json()['wind']
    weather_data = '{}\n' \
           'Temperatura: {} °C\n' \
           'Pressão: {} hPa\n' \
           'Humidade: {} %\n' \
           'Máxima: {} °C\n' \
           'Mínima: {} °C\n' \
           'Velocidade do vento: {} km/h\n'.format(description, weather['temp'], weather['pressure'], weather['humidity'], weather['temp_max'], weather['temp_min'], wind['speed'])

    payload = {'recipient': {'id': sender}, 'message': {'text': weather_data}}
    print(payload)
    send_message(payload)

    return None


#Função root do Flask, rota que se comunica com o webhook do Facebook
@app.route('/', methods=['GET', 'POST'])
def webhook():  
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id']
            print(data)

            if 'message' in data['entry'][0]['messaging'][0]:
                message = data['entry'][0]['messaging'][0]['message']

            else:
                message = 'null'

            #Caso receba as coordenadas
            if 'attachments' in message:
                if 'payload' in message['attachments'][0]:
                    if 'coordinates' in message['attachments'][0]['payload']:
                        location = message['attachments'][0]['payload']['coordinates']
                        latitude = location['lat']
                        longitude = location['long']
                        send_weather_info(sender, latitude=latitude, longitude=longitude)
                        
            #Caso receba uma mensagem de texto    
            elif message != 'null':

                text = '{}'.format(message['text'])
                flag = 0
                for city in CITIES:
                    if text.lower() in city and flag == 0:
                        send_weather_info(sender, city_name=text)
                        flag = 1

                payload = location_quick_reply(sender)
                send_message(payload) 
                

        except Exception as e:
            print(traceback.format_exc())

    #Verificação do Webhook
    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong verify_token"

    return "Emptiness"


if __name__ == '__main__':
	app.run(debug=True)