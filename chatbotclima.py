import os
import json
import traceback
import requests

from cities_list import CITIES
from flask import Flask, request

token = os.environ.get('FB_ACCESS_TOKEN')
api_key = os.environ.get('WEATHER_API_KEY')
app = Flask(__name__)

def location_quick_reply(sender):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": "Compartilhe sua localização:",
            "quick_replies": [
                {
                    "content_type": "location",
                }
            ]
        }
    }

'''def send_attachment(sender, type, payload):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "attachment": {
                "type": type,
                "payload": payload,
            }
        }
    }'''

def send_attachment(sender, payload):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": payload
        }
    }

def send_weather_info(sender, **kwargs):
    latitude = kwargs.pop('latitude', None)
    longitude = kwargs.pop('longitude', None)
    city_name = kwargs.pop('city_name', None)

    if latitude and longitude:
        query = 'lat={}&lon={}'.format(latitude, longitude)
    elif city_name:
        query = 'q={},br'.format(city_name)

    url = 'http://api.openweathermap.org/data/2.5/weather?' \
          '{}&appid={}&units={}&lang={}'.format(query,api_key,'metric','pt')

    r = requests.get(url)

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
    '''if 'visibility' in weather:
            weather_data = 'Visibilidade: {}'.format(weather['visibility'])'''
    payload = {'recipient': {'id': sender}, 'message': {'text': weather_data}}
    '''response = r.json()

    print (response)

    name = response['name']
    weather = response['main']
    wind = response['wind']

    elements = [{
        'title': name,
        'subtitle': 'Temperatura: {} graus'.format(str(weather['temp']).replace('.',',')),
    }]

    for info in response['weather']:
        description = info['description'].capitalize()
        icon = info['icon']

        weather_data = 'Umidade: {}%\n' \
                       'Pressão: {}\n' \
                       'Velocidade do vento: {}'.format(weather['humidity'],
                                                          weather['pressure'],
                                                          wind['speed'])

        if 'visibility' in response:
            weather_data = '{}\n Visibilidade: {}'.format(weather_data, response['visibility'])

        elements.append({
            'title': description,
            'subtitle': weather_data,
            'image_url': 'http://openweathermap.org/img/w/{}.png'.format(icon)
        })

    #payload = send_attachment(sender,'template', {"template_type": "list", "top_element_style": "large", "elements": elements,})
    payload = send_attachment(sender, elements)'''
    send_message(payload)

    return None

def send_message(payload):
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)


@app.route('/', methods=['GET', 'POST'])
def webhook():  
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id'] # Sender ID
            print(data['entry'][0]['messaging'][0])
            if 'message' in data['entry'][0]['messaging'][0]:
                message = data['entry'][0]['messaging'][0]['message']
            else:
                message = 'null'

            if 'attachments' in message:
                if 'payload' in message['attachments'][0]:
                    if 'coordinates' in message['attachments'][0]['payload']:
                        location = message['attachments'][0]['payload']['coordinates']
                        latitude = location['lat']
                        longitude = location['long']
                        send_weather_info(sender, latitude=latitude, longitude=longitude)
            elif message != 'null':

                text = '{}'.format(message['text'])
                flag = 0
                for city in CITIES:
                    if text.lower() in city && flag == 0:
                        send_weather_info(sender, city_name=text)
                        flag = 1
                if flag == 0:
                    payload = location_quick_reply(sender)
                    send_message(payload) 
                

        except Exception as e:
            print(traceback.format_exc())

    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong verify_token"
    return "Nothing"


if __name__ == '__main__':
	app.run(debug=True)