# Calendly Booking Checker
This small tool can check a given Calendly calendar frequently and uses ntfy to inform should there be a new apointment available - or if a previsouly existing one had been removed or booke.

## Adding relevant configuration properties
In order to use this, the configuration values have to be passed via the environment, e.g. using an `.env` file or some other (that have not been tested yet).
The options that need to be configured there are the following:

```
TOPIC = ""
NTFY_TOPIC = ""
NTFY_TOKEN = ""
FORM_URL = ""
CALENDLY_ID = ""
END_MONTH = "2025-12"
```
