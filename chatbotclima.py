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

@app.route('/', methods=['GET', 'POST'])
def webhook():  
    if request.method == 'POST':
        try:
            print("mensagem recebida")
            data = json.loads(request.data.decode())
            print(data)
            sender = data['entry'][0]['messaging'][0]['sender']['id'] # Sender ID
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
                        url = 'http://api.openweathermap.org/data/2.5/weather?' + 'lat={}&lon={}&APPID={}&units={}&lang={}'.format(latitude, longitude, api_key, 'metric', 'pt')

                        r = requests.get(url)

                        description = r.json()['weather'][0]['description'].title()

                        icon = r.json()['weather'][0]['icon']

                        weather = r.json()['main']

                        text_res = '{}\n' \
                                    'Temperatura: {}\n' \
                                    'Pressão: {}\n' \
                                    'Humidade: {}\n' \
                                    'Máxima: {}\n' \
                                    'Mínima: {}'.format(description, weather['temp'], weather['pressure'], weather['humidity'], weather['temp_max'], weather['temp_min'])
                        payload = {'recipient': {'id': sender}, 'message': {'text': text_res}}
                        r = requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)
            else:
                payload = location_quick_reply(sender)
                print("foi no payload")

                r = requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)

        except Exception as e:
            print(traceback.format_exc())

    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('FB_VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong verify token"
    return "Nothing"


if __name__ == '__main__':
	app.run(debug=True)