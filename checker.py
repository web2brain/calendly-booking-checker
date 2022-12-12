import requests
import os
import time
import numpy as np
import pprint as pp
import json
import ast
import smtplib, ssl
# Import the datetime module
import datetime as dt
import calendar
from loguru import logger




## Functions 
def get_last_date_of_month(start_date):
    """
    This function returns the the last date of the month, given a particular
    start date.
    """    
    # Get the year and month of the start date
    
    start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").date()
    year = start_date.year
    month = start_date.month

    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]

    # Return the last date of the month
    return dt.date(year, month, last_day)

def send_notification(subject, body): 
    # Connect to the SMTP server

    server = smtplib.SMTP(SMTP_SERVER, PORT)
    context = ssl.create_default_context()
    server.starttls(context=context) # Secure the connection using the tls protocol 
    server.login(FROM_EMAIL, APP_PASSWORD)

    # Build the email message
    logger.info("Constructing Email Notification Message")
    message = f"From: {FROM_EMAIL}\n"
    message += f"To: {NOTIFICATION_EMAIL}\n"
    message += f"Subject: {subject}\n\n"
    message += body


    # Send the email
    server.sendmail(FROM_EMAIL, NOTIFICATION_EMAIL, message)



if __name__ == "__main__":

    ## Email Setup 
    NOTIFICATION_EMAIL = "" # Add Email Recipient
    FROM_EMAIL = "" # Add Email Sender
    APP_PASSWORD = ""  # Add App Password for Email
    SMTP_SERVER = "smtp.gmail.com" # The SMTP server to use for sending emails
    PORT = 587


    while True:
        
        time.sleep(5) # Check the booking form for changes every 60 seconds
        logger.info("Initializing current datetime")
        start_date = dt.datetime.today().strftime("%Y-%m-%d") # get current data "YYYY-MM-DD"
        end_date = get_last_date_of_month(start_date) # get month end "YYYY-MM-DD"
        logger.info(f"Start Date: {start_date} ")
        logger.info(f"End Date: {end_date}")

                
        # Meeting Booking 
        form_url = "" # Booking form URL
        date_url = "" # XHR Response

        logger.info("Sending request to calendly")
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
                    # print('Available time slot: ', slot['start_time'])
                    # logger.info(f"Slot found at: {slot['start_time']}")
                    current_available_timeslots.append(slot['start_time']) # only rewrite file if changes exist
        logger.info("There are currently {} available slots".format(len(current_available_timeslots)))

        # Retrieve previous available bookings and compare 
        try:
            with open("available_timeslots.txt", "r") as f:
                logger.info("Checking previous available slots")
                previous_schedule = f.read()
                previous_schedule = ast.literal_eval(previous_schedule) # convert list string to list
                logger.info("During the last scan, there were {} available slots".format(len(previous_schedule)))
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
                if timeslot not in current_available_timeslots
            ]
        else:
            added_timeslots = []
            removed_timeslots = []

        # If there are any changes, update the available_timeslots.txt
        if len(added_timeslots) > 0 or len(removed_timeslots) > 0:
            logger.info("Updating available slots")
            with open("available_timeslots.txt", "w") as f:
                # Write the encoded data to the file
                json_data = json.dumps(current_available_timeslots)
                f.write(json_data)

        # Send an email each time a timeslot is added or removed
        for timeslot in added_timeslots:
            logger.info(f"Sending an email notification for added slot: {timeslot}")
            start_time = dt.datetime.fromisoformat(timeslot)
            subject = f"One-to-one Online Shop Business Planning Consultation (OSE-F): New timeslot added on {timeslot}"
            body = f"A new timeslot was added on {start_time:%Y-%m-%d} at {start_time:%I:%M %p}\n at {form_url}"
            send_notification(subject, body)

        for timeslot in removed_timeslots:
            logger.info(f"Sending an email notification for removed slot: {timeslot} ")
            start_time = dt.datetime.fromisoformat(timeslot)
            subject = f" One-to-one Online Shop Business Planning Consultation (OSE-F): Timeslot {timeslot} has been booked"
            body = f"Timeslot {start_time:%Y-%m-%d} at {start_time:%I:%M %p} has been booked at {form_url}"
            send_notification(subject, body)


