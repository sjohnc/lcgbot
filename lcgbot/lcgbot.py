import json
import os
import requests
import time
from slackclient import SlackClient

#In Memory Storage for now
CARDS = None

def populate_cards():
    global CARDS
    r = requests.get('https://api.fiveringsdb.com/cards')
    if r.status_code == 200:
        CARDS = r.json()['records']
    else:
        file_path = os.path.join(os.path.dirname(__file__), 'cards.json')
        with open(file_path) as f:
            CARDS = json.load(f)['records']

def get_matching_card(name):
    global CARDS
    all_cards = [c for c in CARDS if name.lower() in c['name_canonical'].lower()]
    first_card = all_cards[0] if len(all_cards) else None
    return first_card

def slackify_text(text):
    text = text.replace('<b>', '*')
    text = text.replace('</b>', '*')
    text = text.replace('<em>', '*_')
    text = text.replace('</em>', '_*')
    text = text.replace('<i>', '_')
    text = text.replace('</i>', '_')
    text = text.replace('[', ':')
    text = text.replace(']', ':')
    return text

def make_key_value(key, value):
    if key is not None and key is not 'None' and value is not None and value is not 'None' and value != '':
        return '{}: {}\n'.format(key, value)
    else:
        return ''

def get_field(card, field, name = None, do_title = False):
    value = card.get(field)
    if value is None:
        return ''
    value = str(value).encode('utf-8')
    if do_title:
        value = value.title()
    name = name if name else field
    return make_key_value(name.title(), value)

def get_traits(card):
    traits = ", ".join(map(str,card.get('traits', []))).title().encode('utf-8')
    return make_key_value('Traits', traits)

def get_text(card):
    text = card.get('text')
    if text is None:
        return ''
    text = slackify_text(text.encode('utf-8'))
    return make_key_value('Text', text)

def get_image(card):
    try:
        image = str([c['image_url'] for c in card['pack_cards'] if 'image_url' in c][0])
        return make_key_value('Image', image)
    except:
        return ''

def get_pack(card):
    try:
        pack = str([c['pack']['id'] for c in card['pack_cards'] if 'id' in c['pack']][0])
        return make_key_value('Pack', pack.title())
    except:
        return ''

def pprint_card(card):
    pprinted = ''
    pprinted += get_field(card, 'name')
    pprinted += get_pack(card)
    pprinted += get_field(card, 'type', do_title = True)
    pprinted += get_field(card, 'side', name = 'deck', do_title = True)
    pprinted += '\n'
    pprinted += get_field(card, 'cost')
    pprinted += get_field(card, 'military')
    pprinted += get_field(card, 'military_bonus', 'military')
    pprinted += get_field(card, 'political')
    pprinted += get_field(card, 'political_bonus', 'political')
    pprinted += get_field(card, 'glory')
    pprinted += '\n'
    pprinted += get_traits(card)
    pprinted += '\n'
    pprinted += get_text(card)
    pprinted += '\n'
    pprinted += get_image(card)
    return pprinted.replace('\n\n\n', '\n\n')

if __name__ == '__main__':
    trigger = "!card"
    offset = len(trigger) + 1
    populate_cards()
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    sc = SlackClient(slack_token)
    if sc.rtm_connect():
        while True:
            msgs = sc.rtm_read()
            for msg in msgs:
                if msg.get('text') is not None and '!card' in msg.get('text'):
                    txt = msg['text']
                    name = txt[txt.find(trigger)+offset:]
                    card = get_matching_card(name)
                    response = 'Card not found'
                    if card is not None:
                        response = pprint_card(card)
                        print response
                    sc.api_call(
                        'chat.postMessage',
                        channel=msg.get('channel'),
                        text=response
                    )
            time.sleep(1)
    else:
        print "Connection failed"
