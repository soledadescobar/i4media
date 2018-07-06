import logging

from raven.handlers.logging import SentryHandler
from raven.conf import setup_logging


# Sentry Handler Configuration
handler = SentryHandler(
    'https://b4ee7fc7ce70412b9142fee18f9a2f31:344832efb44a4f8e9d784cbafd55192f@sentry.io/1238784'
)

handler.setLevel(logging.ERROR)

setup_logging(handler)