# lcgbot

Slack-based bot that can query APIs provided by card databases listed below.

## Supported APIs

* https://fiveringsdb.com via https://alsciende.github.io/fiveringsdb-api
* https://netrunnerdb.com via https://netrunnerdb.com/api/2.0/doc
* https://swdestinydb.com via https://swdestinydb.com/api

## Usage

### Chat

The bot will detect the trigger ``<<``name``>>`` where name is the card name you wish to lookup. It uses a fuzzy matching algorithm such that your name doesn't have to be exact.
