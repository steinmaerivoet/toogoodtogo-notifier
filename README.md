# Too Good To Go Notifier

## About
[Too Good To Go](https://toogoodtogo.be/) is a platform for local food stores and restaurants to reduce food waste.
The goal is to save meals which are close to their due date.
Stores can make items available for reservation with discounts. 
Bringing your own package is required!


This application is a simple [scheduler](https://schedule.readthedocs.io/) which tracks new available items on Too Good To Go.
It uses an [unofficial API client](https://github.com/ahivert/tgtg-python) by Anthony Hivert to check for new available items.

To deploy the application I use Docker Compose to run my python scheduler and a MongoDB containerized. 
I gathered some inspiration from a [docker blog](https://www.docker.com/blog/containerized-python-development-part-1/) and [Awesome Compose](https://github.com/docker/awesome-compose/tree/master/nginx-flask-mongo).

## Install
- `git clone https://github.com/steinmaerivoet/toogoodtogo-notifier.git`
- Add `tgtg.conf` to `scheduler/`
  ```
  [tgtg]
  email =
  password =
  
  [mongo]
  host =
  port =
  username =
  password =
  database =
  
  [callback]
  url =
  
  [scheduler]
  sync_interval_seconds =
  ```      
- Add `.env` to `./` to add MongoDB credentials as [environment variables](https://docs.docker.com/compose/environment-variables/). 
  ```
  MONGO_USERNAME=
  MONGO_PASSWORD=
   ```
- Run `docker-compose build`
- Run `docker-compose up -d`

The Mongo DB service is exposed at port `27888` for local access.

