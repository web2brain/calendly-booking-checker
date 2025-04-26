import requests
import os
import time
import numpy as np
import pprint as pp
import json
import ast
import smtplib, ssl
import datetime as dt
import calendar
from loguru import logger
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta

def send_notification(subject, message, form_url, date):

    logger.info(f"Constructing ntfy notification message for {form_url}?month={date:%Y-%m}&date={date:%Y-%m-%d}")
    requests.post(NTFY_TOPIC,
    data=message,
    headers={
        "Authorization": f"Bearer {NTFY_TOKEN}",
        "Title": "New appointment available",
        "Priority": "urgent",
        "Tags": "calendar",
        "Click": f"{form_url}?month={date:%Y-%m}&date={date:%Y-%m-%d}"
    })



def checkMonth(date):

        logger.info("Initializing current datetime")
        start_date = date.strftime("%Y-%m-%d") # get current data "YYYY-MM-DD"
        end_date = (date + relativedelta(day=31)).strftime("%Y-%m-%d")
        logger.info(f"Start Date: {start_date} ")
        logger.info(f"End Date: {end_date}")


        # Meeting Booking
        form_url = FORM_URL # Booking form URL
        date_url = f"https://calendly.com/api/booking/event_types/{CALENDLY_ID}/calendar/range?timezone=Europe%2FBerlin&diagnostics=false&range_start={start_date}&range_end={end_date}"# XHR Response

        logger.info("Sending request to calendly " + date_url)
        r = requests.get(date_url)
        response = r.json()
        logger.info("Response recieved")

        # Check Current Available Bookings
        current_available_timeslots = []
        days = len(response['days'])
        logger.info("Checking for available booking slots")
        for i in range(0, days):
            if response['days'][i]['status'] == 'available':
                for slot in response['days'][i]['spots']:
                     print('Available time slot: ', slot['start_time'])
                     logger.info(f"Slot found at: {slot['start_time']}")
                     current_available_timeslots.append(slot['start_time']) # only rewrite file if changes exist
        logger.info("There are currently {} available slots".format(len(current_available_timeslots)))

        # Retrieve previous available bookings and compare
        try:
            with open("available_timeslots.txt", "r") as f:
                logger.info("Checking previous available slots")
                previous_schedule = f.read()
                previous_schedule = ast.literal_eval(previous_schedule) # convert list string to list
                logger.info("Currently there are {} available slots known from previous scans".format(len(previous_schedule)))
        except FileNotFoundError:
            print("No prior schedule exists")
            previous_schedule = ""



        # Compare the current schedule to the previous schedule
        if current_available_timeslots != previous_schedule:
            logger.info("Bookings have changed since the last scan")
            # The schedule has changed, so check for added or removed timeslots
            added_timeslots = [
                timeslot for timeslot in current_available_timeslots
                if timeslot not in previous_schedule
            ]

            removed_timeslots = [
                timeslot for timeslot in previous_schedule
                if (timeslot not in current_available_timeslots and timeslot >= start_date and timeslot <= end_date)
            ]

            other_timeslots = [
                timeslot for timeslot in previous_schedule
                if ((timeslot < start_date or timeslot > end_date))
            ]
        else:
            added_timeslots = []
            removed_timeslots = []

        # If there are any changes, update the available_timeslots.txt
        if len(added_timeslots) > 0 or len(removed_timeslots) > 0:
            logger.info("Updating available slots")
            with open("available_timeslots.txt", "w") as f:
                # Write the encoded data to the file
                json_data = json.dumps(current_available_timeslots + other_timeslots)
                f.write(json_data)

        # Send a notification each time a timeslot is added or removed
        for timeslot in added_timeslots:
            logger.info(f"Sending an ntfy notification for added slot: {timeslot}")
            start_time = dt.datetime.fromisoformat(timeslot)
            subject = f"{TOPIC}: New timeslot added on {timeslot}"
            message = f"A new timeslot was added on {start_time:%Y-%m-%d} at {start_time:%H:%M} at {form_url}"
            send_notification(subject, message, form_url, start_time)

        for timeslot in removed_timeslots:
            logger.info(f"Sending an ntfy notification for removed slot: {timeslot} ")
            start_time = dt.datetime.fromisoformat(timeslot)
            subject = f"{TOPIC}: Timeslot {timeslot} has been booked"
            body = f"Timeslot {start_time:%Y-%m-%d} at {start_time:%H:%M} has been removed at {form_url}"
            send_notification(subject, body, form_url, start_time)

if __name__ == "__main__":

    ## Setup
    load_dotenv()
    TOPIC = os.getenv('TOPIC')
    NTFY_TOPIC = os.getenv('NTFY_TOPIC')
    NTFY_TOKEN = os.getenv('NTFY_TOKEN')
    FORM_URL = os.getenv('FORM_URL')
    CALENDLY_ID = os.getenv('CALENDLY_ID')
    END_MONTH = os.getenv('END_MONTH')

    while True:
        start_date = dt.datetime.today()
        end_month = dt.datetime.strptime(END_MONTH, "%Y-%m") + relativedelta(day=31)
        while start_date <= end_month:
            logger.info(f"Getting available slots from {start_date:%Y-%m-%d}")
            checkMonth(start_date)
            time.sleep(60) # Check the booking form for changes every 60 seconds
            start_date = (start_date.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
