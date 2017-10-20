# This Python file uses the following encoding: utf-8
import json
import os
import requests
import time
from slackclient import SlackClient
from socket import error as socket_error

#In Memory Storage for now
CARDS = None

colors = {
        'crab': "#001c94",
        'crane': "#0089de",
        'dragon': "#00a472",
        'lion': "#cb9d00",
        'phoenix': "#c16400",
        'scorpion': "#a61600",
        'unicorn': "#780098",
        }

def populate_cards():
    global CARDS
    file_path = os.path.join(os.path.dirname(__file__), 'cards.json')
    try:
        r = requests.get('https://api.fiveringsdb.com/cards')
        if r.status_code == 200:
            CARDS = r.json()['records']
            with open(file_path, 'w') as f:
                json.dump(CARDS, f)
        else:
            raise RuntimeError("API Call not OK")
    except:
        with open(file_path) as f:
            CARDS = json.load(f)

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

def get_field(card, field, do_title = False):
    value = card.get(field)
    if value is None:
        return ''
    unique = ''
    if card.get("unicity") and field == 'name':
        unique = u'◦ '
    if do_title:
        value = value.title()
    value = u'{}{}'.format(unique,value).encode('utf-8')
    return value

def get_traits(card):
    traits = ", ".join(map(str,card.get('traits', []))).title().encode('utf-8')
    return traits

def get_text(card):
    text = card.get('text')
    if text is None:
        return ''
    text = slackify_text(text.encode('utf-8'))
    return text

def get_image(card):
    try:
        image = str([c['image_url'] for c in card['pack_cards'] if 'image_url' in c][0])
        return image
    except:
        return ''

def get_pack(card):
    try:
        pack = str([c['pack']['id'] for c in card['pack_cards'] if 'id' in c['pack']][0])
        return pack.title()
    except:
        return ''

def get_number(card):
    try:
        pack = str([c['position'] for c in card['pack_cards'] if 'position' in c][0])
        return pack.title()
    except:
        return ''

def get_color(card):
    clan = card.get('clan')
    return colors.get(clan, '#3c3c3c')

def pprint_card(card):
    pprinted = ''
    pprinted += make_key_value('Name', get_field(card, 'name'))
    pprinted += make_key_value('Pack', get_field(card, 'pack'))
    pprinted += make_key_value('Type', get_field(card, 'type', do_title = True))
    pprinted += make_key_value('Deck', get_field(card, 'side', do_title = True))
    pprinted += '\n'
    pprinted += make_key_value('Cost', get_field(card, 'cost'))
    pprinted += make_key_value('Military', get_field(card, 'military'))
    pprinted += make_key_value('Military', get_field(card, 'military_bonus'))
    pprinted += make_key_value('Political', get_field(card, 'political'))
    pprinted += make_key_value('Political', get_field(card, 'political_bonus'))
    pprinted += make_key_value('Glory', get_field(card, 'glory'))
    pprinted += '\n'
    pprinted += make_key_value('Traits', get_traits(card))
    pprinted += '\n'
    pprinted += make_key_value('Text', get_text(card))
    pprinted += '\n'
    pprinted += make_key_value('Image', get_image(card))
    return pprinted.replace('\n\n\n', '\n\n')

def make_title_value(card, key, name = None, value = None, short = True):
    name = name if name else key.title()
    value = value if value else get_field(card, key)
    if value is not None and value != 'None' and value != '':
        return {
                "title": name,
                "value": value,
                "short": short
                }
    else:
        return None


def make_card_attachment(card):
    fields = ['cost', ('military', 'military_bonus'), 'glory',
            ('political', 'political_bonus'), 'influence']
    attachment_fields = []
    for field in fields:
        if isinstance(field, tuple):
            k,v = field
            res = get_field(card, k)
            if res is not None and res != 'None' and res != '':
                attachment_fields.append(make_title_value(card, k))
            else:
                attachment_fields.append(make_title_value(card, v, name = k.title()))
        else:
            attachment_fields.append(make_title_value(card, field))
    attachment_fields.append(make_title_value(card, 'traits', name = 'Traits', value = get_traits(card)))
    attachment_fields.append(make_title_value(card, 'text', name = 'Text', value = get_text(card), short = False))
    attachment_fields = [f for f in attachment_fields if f is not None]
    return {
            "fallback": get_field(card, 'name'),
            "color": get_color(card),
            "author_name": "{clan} - {side} - {card_type} [{pack} {number}]".format(
                clan = get_field(card, 'clan', do_title = True),
                side = get_field(card, 'side', do_title = True),
                card_type = get_field(card, 'type', do_title = True),
                pack = get_pack(card),
                number = get_number(card)
                ),
            "title": get_field(card, 'name'),
            "title_link": "https://fiveringsdb.com/card/{}".format(get_field(card, 'id')),
            "fields": attachment_fields,
            "image_url": get_image(card),
            "mrkdwn_in": ['fields']
            }

def find_rulings(name):
    card_id = get_matching_card(name)['id']
    r = requests.get('https://api.fiveringsdb.com/cards/{}/rulings'.format(card_id))
    if r.status_code == 200:
        return r.json()['records']

def make_ruling_attachments(rulings):
    return [{
            "fallback": 'Rulings',
            "color": '#363636',
            "author_name": rule['source'],
            "title": 'Rulings',
            "text": rule.get('text'),
            "title_link": rule.get('link', 'No link Available'),
            "mrkdwn_in": ['text']
            } for rule in rulings]

if __name__ == '__main__':
    card_trigger = "!card"
    card_offset = len(card_trigger) + 1
    rule_trigger = "!rule"
    rule_offset = len(rule_trigger) + 1
    populate_cards()
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    sc = SlackClient(slack_token)
    while True:
        try:
            if sc.rtm_connect():
                print 'Successfully connected'
                while True:
                    msgs = sc.rtm_read()
                    for msg in msgs:
                        if msg.get('text') is not None and card_trigger in msg.get('text'):
                            print 'Received card trigger'
                            txt = msg['text']
                            name = txt[txt.find(card_trigger)+card_offset:]
                            card = get_matching_card(name)
                            response = 'Card not found'
                            if card is not None:
                                response = make_card_attachment(card)
                            sc.api_call(
                                'chat.postMessage',
                                channel=msg.get('channel'),
                                attachments=[response]
                            )
                        if msg.get('text') is not None and rule_trigger in msg.get('text'):
                            print 'Received rule trigger'
                            txt = msg['text']
                            name = txt[txt.find(rule_trigger)+rule_offset:]
                            rulings = find_rulings(name)
                            response = 'Ruling not found'
                            if rulings is not None:
                                response = make_ruling_attachments(rulings)
                            sc.api_call(
                                'chat.postMessage',
                                channel=msg.get('channel'),
                                attachments=response
                            )
                    time.sleep(1)
            else:
                print "Connection failed"
                time.sleep(5)
        except socket_error,e:
            print "Connection error:",e
            time.sleep(5)
        except Exception, e:
            print "other eror:",e
            time.sleep(5)
