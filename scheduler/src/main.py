from pymongo import MongoClient
from tgtg import TgtgClient
from tgtg import TgtgAPIError
from tgtg import TgtgLoginError
from event import Event
import json
from datetime import datetime
import schedule
import time
import requests
import configparser
import logging

LOGGING_FORMAT = '%(asctime)-15s %(message)s'


def main():
    # setup application
    config = configparser.ConfigParser()
    config.read('scheduler/tgtg.conf')
    config.sections()
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT)

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

    # setup callback url
    callback_url = config['callback']['url']

    scheduler_interval = config['scheduler'].getint('sync_interval_seconds')
    schedule.every(scheduler_interval).seconds.do(job, tgtg_client, events_collection, callback_url)

    while True:
        schedule.run_pending()
        time.sleep(1)


def new_item_available(new_event, events_collection):
    document_filter = {"store": new_event.store,
                       "pickup_start_time": new_event.pickup_start_time}
    return (new_event.items_available != 0) & (events_collection.count_documents(document_filter, limit=1) == 0)


def item_updated(new_event, events_collection):
    document_filter = {"store": new_event.store,
                       "items_available": new_event.items_available,
                       "pickup_start_time": new_event.pickup_start_time}
    return events_collection.count_documents(document_filter, limit=1) == 0


def insert_new_event(new_event, events_collection):
    events_collection.insert_one(vars(new_event))
    logging.info("inserted new event")


def create_event(item):
    store = item.get("store").get("store_name")
    items_available = item.get("items_available")
    pickup_start_time = item.get("pickup_interval", {}).get("start", None)
    pickup_end_time = item.get("pickup_interval", {}).get("end", None)
    return Event(datetime.now(), store, items_available, pickup_start_time, pickup_end_time)


def fire_event(new_event, callback_url):
    data = json.dumps(new_event.__dict__, default=str)
    headers = {'Content-type': 'application/json'}
    requests.post(url=callback_url, data=data, headers=headers)


def job(tgtg_client, events_collection, callback_url):
    logging.info("syncing items...")

    # get favorite items
    try:
        items = tgtg_client.get_items()

        for item in items:
            new_event = create_event(item)

            if new_item_available(new_event, events_collection):
                fire_event(new_event, callback_url)
                logging.info("event fired!")

            if item_updated(new_event, events_collection):
                # store in database
                insert_new_event(new_event, events_collection)
                logging.info("items in store %s updated with quantity %s", new_event.store, new_event.items_available)

    except TgtgLoginError as tgtgLoginError:
        logging.error("TGTG login error: %s", tgtgLoginError.args)
    except TgtgAPIError as tgtgAPIError:
        logging.error("TGTG API error: %s", tgtgAPIError.args)
    except requests.exceptions.ConnectionError as connectionError:
        logging.error("TGTG connection error: %s", connectionError.response)


if __name__ == "__main__":
    main()
