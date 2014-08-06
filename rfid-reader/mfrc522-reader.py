#!/usr/bin/env python
# -*- coding: utf8 -*-

import RPi.GPIO as GPIO
import signal
import sys
import time
import requests
import logging
import multiprocessing
from MFRC522 import MFRC522
from uuid import getnode

API_ENDPOINT = 'http://localhost:5000/vote'
API_TIMEOUT = 2

GPIO_LED_0, GPIO_LED_1 = 11, 12 

class Reader(multiprocessing.Process):

    def __init__(self, spi_device, led_pin):
        self.spi_device = spi_device
        self.led_pin = led_pin
        super(Reader, self).__init__()

    def run(self):

        logger = multiprocessing.get_logger()

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.led_pin, GPIO.OUT)
        GPIO.output(self.led_pin, True)

        reader = MFRC522(self.spi_device)

        while True:

            reader.MFRC522_Request(reader.PICC_REQIDL)
            (status, data) = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                vote = {
                    'tag_id': "%0.2x%0.2x%0.2x%0.2x" % (data[0], data[1], data[2], data[3]),
                    'timestamp': time.time(),
                    'voting_machine_id': getnode(),  # see RFC 4122
                    'spi_device': self.spi_device,
                }
                if self.submit_vote(vote):
                    logger.info('Vote submitted %s', vote)
                    self.led_blink()
                else:
                    logger.error('Could not submit vote %s', vote)

    def submit_vote(self, vote):
        try:
            req = requests.post(API_ENDPOINT, data=vote, timeout=API_TIMEOUT)
            if req.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        return False

    def led_blink(self, times=2):
        for i in xrange(times):
            GPIO.output(self.led_pin, False)
            time.sleep(0.1)
            GPIO.output(self.led_pin, True)
            time.sleep(0.1)


if __name__ == '__main__':

    def sig_handler(signal, frame):
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(multiprocessing.SUBDEBUG)

    GPIO.setwarnings(False)

    Reader('/dev/spidev0.0', GPIO_LED_0).start()
    Reader('/dev/spidev0.1', GPIO_LED_1).start()
