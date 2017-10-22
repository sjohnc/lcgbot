# This Python file uses the following encoding: utf-8
import json
import os
import re
import requests
import time

from slackclient import SlackClient
from socket import error as socket_error

#In Memory Storage for now
CARDS = None
SWCARDS = None

colors = {
        'crab': "#001c94",
        'crane': "#0089de",
        'dragon': "#00a472",
        'lion': "#cb9d00",
        'phoenix': "#c16400",
        'scorpion': "#a61600",
        'unicorn': "#780098",
        }

swcolors = {
        'red': "##b22222",
        'yellow': "#dab032",
        'blue': "#0b609e",
        'gray': "#979d9f",
}

pattern = '^([-+]?)(\d*?)([-A-Z][a-zA-Z]?)(\d*?)$'
dice_pattern = re.compile(pattern)

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

def populate_swcards():
    global SWCARDS
    file_path = os.path.join(os.path.dirname(__file__), 'swcards.json')
    try:
        r = requests.get('https://swdestinydb.com/api/public/cards')
        if r.status_code == 200:
            SWCARDS = r.json()
            with open(file_path, 'w') as f:
                json.dump(SWCARDS, f)
        else:
            raise RuntimeError("API Call not OK")
    except:
        with open(file_path) as f:
            SWCARDS = json.load(f)

# swexample = {
#             "sides": ["1RD", "2RD", "1F", "1Dc", "1R", "-"],
#     "set_code": "AW",
#             "set_name": "Awakenings",
#     "type_code": "character",
#         "type_name": "Character",
#         "faction_code": "red", # determines color of msg
#     "faction_name": "Command",
#     "affiliation_code": "villain",
#         "affiliation_name": "Villain",
#         "rarity_code": "L",
#     "rarity_name": "Legendary",
#     "position": 1,
#     "code": "01001",
#     "ttscardid": "1300",
#     "name": "Captain Phasma",
#     "subtitle": "Elite Trooper",
#         "cost": null,
#         "health": 11,
#         "points": "12\/15",
#             "text": "Your non-unique characters have the Guardian keyword.",
#     "deck_limit": 1,
#     "flavor": "\"Whatever you're planning, it won't work.\"",
#     "illustrator": "Darren Tan",
#         "is_unique": true,
#         "has_die": true,
#         "has_errata": false,
#         "url": "https:\/\/swdestinydb.com\/card\/01001",
#         "imagesrc": "https:\/\/swdestinydb.com\/bundles\/cards\/en\/01\/01001.jpg",
#         "label": "Captain Phasma - Elite Trooper",
#     "cp": 1215
# }

('cost', 'health', 'points', )

def get_matching_card(name):
    global CARDS
    all_cards = [c for c in CARDS if name.lower() in c['name_canonical'].lower()]
    first_card = all_cards[0] if len(all_cards) else None
    return first_card

def get_matching_swcard(name):
    global SWCARDS
    all_cards = [c for c in SWCARDS if name.lower() in c['label'].lower()]
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

# def make_key_value(key, value):
#     if key is not None and key is not 'None' and value is not None and value is not 'None' and value != '':
#         return '{}: {}\n'.format(key, value)
#     else:
#         return ''

def get_field(card, field, do_title = False):
    value = card.get(field)
    if value is None:
        return ''
    unique = ''
    if card.get("unicity") and field == 'name':
        unique = u'◦ '
    if card.get("is_unique") and field == 'label':
        unique = ':unique: '
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

def make_dice(die):
    # die: list of strings
    codes = {
        '-': 'blank',
        'MD': 'melee',
        'RD': 'ranged',
        'ID': 'indirect',
        'Dr': 'disrupt',
        'Dc': 'discard',
        'F': 'focus',
        'R': 'resource',
        'Sp': 'special',
        'Sh': 'shield',
        'X': ''
    }
    sides = []
    for side in die:
        elems = dice_pattern.match(str(side))
        modifier = elems.group(1)
        value = elems.group(2)
        code = elems.group(3)
        icon = ':{}:'.format(codes.get(code))
        cost = '{}:resource:'.format(elems.group(4)) if elems.group(4) else elems.group(4)
        sides.append(modifier + value + icon + cost)
    sides = '[' + '] ['.join(sides) + ']'
    return sides

def get_health(card):
    health = get_field(card, 'health')
    if health:
        return 'Health: {}'.format(health)
    else:
        return ''

def get_points(card):
    points = get_field(card, 'points')
    if points:
        return 'Points: {}'.format(points)
    else:
        return ''

def get_subtype(card):
    subtype = get_field(card, 'subtype_name', True)
    if subtype:
        return ' - {}'.format(subtype)
    else:
        return ''

def build_swfields(card):
    fields = []
    cost = get_field(card, 'cost')
    if cost:
        field_cost = {
                        "title": "Cost",
                        "value": "{} :resource:".format(cost),
                        "short": True
                    }
        fields.append(field_cost)
    sides = make_dice(card.get('sides', []))
    if sides != '[]':
        field_sides = {
                        "value": sides,
                        "short": False
                    }
        fields.append(field_sides)
    text = get_field(card, 'text')
    if text:
        field_text = {
                        "value": slackify_text(text.encode('utf-8')),
                        "short": False
                    }
        fields.append(field_text)
    return fields

# def pprint_card(card):
#     pprinted = ''
#     pprinted += make_key_value('Name', get_field(card, 'name'))
#     pprinted += make_key_value('Pack', get_field(card, 'pack'))
#     pprinted += make_key_value('Type', get_field(card, 'type', do_title = True))
#     pprinted += make_key_value('Deck', get_field(card, 'side', do_title = True))
#     pprinted += '\n'
#     pprinted += make_key_value('Cost', get_field(card, 'cost'))
#     pprinted += make_key_value('Military', get_field(card, 'military'))
#     pprinted += make_key_value('Military', get_field(card, 'military_bonus'))
#     pprinted += make_key_value('Political', get_field(card, 'political'))
#     pprinted += make_key_value('Political', get_field(card, 'political_bonus'))
#     pprinted += make_key_value('Glory', get_field(card, 'glory'))
#     pprinted += '\n'
#     pprinted += make_key_value('Traits', get_traits(card))
#     pprinted += '\n'
#     pprinted += make_key_value('Text', get_text(card))
#     pprinted += '\n'
#     pprinted += make_key_value('Image', get_image(card))
#     return pprinted.replace('\n\n\n', '\n\n')

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

def make_swcard_attachment(card):
    print('making attachment')
    fallback = get_field(card, 'label', True)
    print('fallback')
    color = swcolors[get_field(card, 'faction_code')]
    print('color')
    author_name = '. '.join([get_field(card, 'affiliation_name', True), get_field(card, 'faction_name', True), get_field(card, 'rarity_name', True)])
    print('author_name')
    title = get_field(card, 'label', True)
    print('title')
    title_link = get_field(card, 'url')
    print('title_link')
    text = "*{} {} {} {}*".format(get_field(card, 'type_name', True), get_subtype(card), get_health(card), get_points(card))
    print('text')

    fields = build_swfields(card)
    print('built fields')

    image_url = get_field(card, 'imgsrc')
    print('image url')
    footer = ':{}: {} #{}'.format(get_field(card, 'set_code'), get_field(card, 'set_name'), get_field(card, 'position'))
    print('footer')
    mrkdwn_in = ['fields', 'text', 'footer', 'title', 'fallback']
    ret = [
        {
            "fallback": fallback,
            "color": color,
            "title": title,
            "title_link": title_link,
            "text": text,
            "fields": fields,
            "image_url": image_url,
            "footer": footer,
            "mrkdwn_in": mrkdwn_in,
        }
    ]
    print('ret attach')
    return ret


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

def handle_rule(txt):
    print 'Received rule trigger'
    txt = msg['text']
    name = txt[txt.find(l5rrule_trigger)+l5rrule_offset:]
    rulings = find_rulings(name)
    response = 'Ruling not found'
    if rulings is not None:
        response = make_ruling_attachments(rulings)
    return response

def handle_card(txt):
    print 'Received card trigger'
    name = txt[txt.find(l5rcard_trigger)+l5rcard_offset:]
    card = get_matching_card(name)
    response = 'Card not found'
    if card is not None:
        response = [make_card_attachment(card)]
    return [response]

def handle_swcard(txt):
    print 'Received swcard trigger'
    name = txt[txt.find(swcard_trigger)+swcard_offset:]
    card = get_matching_swcard(name)
    response = 'Card not found'
    if card is not None:
        response = make_swcard_attachment(card)
    return response

if __name__ == '__main__':
    l5rcard_trigger = "!card"
    l5rcard_offset = len(l5rcard_trigger) + 1
    swcard_trigger = "!swcard"
    swcard_offset = len(swcard_trigger) + 1
    l5rrule_trigger = "!rule"
    l5rrule_offset = len(l5rrule_trigger) + 1
    refresh_trigger = "!refreheash"
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    sc = SlackClient(slack_token)
    while True:
        try:
            if sc.rtm_connect():
                populate_cards()
                populate_swcards()
                print 'Successfully connected'
                while True:
                    msgs = sc.rtm_read()
                    for msg in msgs:
                        response = None
                        txt = msg.get('text')
                        if msg.get('text') is not None and l5rcard_trigger in msg.get('text'):
                            response = handle_card(txt)
                        if txt is not None and l5rrule_trigger in msg.get('text'):
                            response = handle_rule(txt)
                        if txt is not None and swcard_trigger in txt:
                            response = handle_swcard(txt)
                        if txt is not None and refresh_trigger in msg.get('text'):
                            populate_cards()
                            populate_swcards()
                            sc.api_call(
                                'chat.postMessage',
                                channel=msg.get('channel'),
                                text="Refreshed DB"
                            )
                        if response is not None:
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
