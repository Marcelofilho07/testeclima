import os
import json
import traceback
import requests

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

    response = r.json()

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

    payload = send_attachment(sender,
                              'template',
                              {
                                  "template_type": "list",
                                  "top_element_style": "large",
                                  "elements": elements,
                              })

    send_message(payload)
    return None

def send_message(payload):
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)


@app.route('/', methods=['GET', 'POST'])
def webhook():  
    if request.method == 'POST':
        try:
            print("mensagem recebida")
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id'] # Sender ID
            print(data)
            if 'message' in data['entry'][0]['messaging'][0]:
                message = data['entry'][0]['messaging'][0]['message']

            #location_quick_reply(857422447981948)
            print("flag 1")
            if 'attachments' in message:
                if 'payload' in message['attachments'][0]:
                    if 'coordinates' in message['attachments'][0]['payload']:
                        location = message['attachments'][0]['payload']['coordinates']
                        latitude = location['lat']
                        longitude = location['long']
                        print("flag 3")
                        send_weather_info(sender, latitude=latitude, longitude=longitude)
            else:
                payload = location_quick_reply(sender)
                send_message(payload) 

        except Exception as e:
            print(traceback.format_exc())

    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "eu amo a lenise <3"
    return "Nothing"


if __name__ == '__main__':
	app.run(debug=True)