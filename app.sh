#!/bin/bash
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN:=$(cat token)}
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN} python lcgbot/lcgbot.py

