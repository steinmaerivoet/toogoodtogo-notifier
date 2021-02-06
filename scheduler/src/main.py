from pymongo import MongoClient
from tgtg import TgtgClient
from event import Event
import json
from datetime import datetime
import schedule
import time
import requests
import configparser
import logging


config = configparser.ConfigParser()
config.read('tgtg.conf')
config.sections()

# setup TGTG
email = config['tgtg']['email']
password = config['tgtg']['password']
tgtg_client = TgtgClient(email=email, password=password)
logging.info("Connected to TGTG service with user %s", email)

# setup Mongo client
host = config['mongo']['host']
port = config['mongo'].getint('port')
username = config['mongo']['username']
password = config['mongo']['password']
database = config['mongo']['database']
mongo_client = MongoClient(host=host, port=port, username=username, password=password)
tgtg_db = mongo_client[database]
events_collection = tgtg_db["events"]
logging.info("Connected to Mongo DB %s", database)

#setup callback url
callbackUrl = config['callback']['url']

def new_item_available(new_event):
    return (new_event.items_available != 0) & (events_collection.count_documents({"store": new_event.store, "pickup_start_time": new_event.pickup_start_time}, limit=1) == 0)

def item_updated(new_event):
    return events_collection.count_documents({"store": new_event.store, "items_available": new_event.items_available, "pickup_start_time": new_event.pickup_start_time}, limit=1) == 0

def insert_new_event(new_event):
    events_collection.insert_one(vars(new_event))
    logging.info("inserted new event")

def create_event(item):
    store = item.get("store").get("store_name")
    items_available = item.get("items_available")
    pickup_start_time = item.get("pickup_interval", {}).get("start", None)
    pickup_end_time = item.get("pickup_interval", {}).get("end", None)
    return Event(datetime.now(), store, items_available, pickup_start_time, pickup_end_time)

def fire_event(new_event):
    data = json.dumps(new_event.__dict__, default=str)
    headers = {'Content-type': 'application/json'}
    requests.post(url=callbackUrl, data=data, headers=headers)

def job():
    logging.info("syncing items...")

    # get favorite items
    items = tgtg_client.get_items()

    for item in items:
        new_event = create_event(item)

        if new_item_available(new_event):
            fire_event(new_event)
            logging.info("event fired!")

        if item_updated(new_event):
            # store in database
            insert_new_event(new_event)
            logging.info("items in store %s updated with quantity %s", new_event, new_event.items_available)


scheduler_interval = config['scheduler'].getint('sync_interval_seconds')
schedule.every(scheduler_interval).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
