
import sys
import time
import logging
from twitchbot_grandmaster import TwitchChat, TwitchBot, TwitchGame
import traceback
import signal

logger = logging.getLogger("bot_manager")
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt)

logger.addHandler(ch)

crawlDict = {}
MAX_CURRENT_CRAWLS = 300

def signal_term_handler(signal, frame):
    raise Exception("SIGSIG")

signal.signal(signal.SIGTERM, signal_term_handler)


try:
	while True:
		#check dead
		channelNeims = crawlDict.keys()
		for name in channelNeims:

			logger.debug("Checking alive channel " + name + "...")

			iCrawl = crawlDict[name]
			if iCrawl.stop:
				logger.info("Channel " + name + " is dead or smth")
				del crawlDict[name]

			elif not iCrawl.channel.is_live():

				logger.info("Channel " + name + " is offline")
				iCrawl.stop_bot()
				del crawlDict[name]
				logger.info("Stopping "+name+" crawler")
			
		#add new channels
		if len(crawlDict) < MAX_CURRENT_CRAWLS:
			logger.debug("Not enough channerals...")
			channels = TwitchChat.get_live_channels("en", limit=MAX_CURRENT_CRAWLS + 8)

			for iChannel in channels:
				if iChannel.name not in crawlDict:
					iCrawl = TwitchBot(iChannel)
					
					logger.info("Starting crawl of channel " + iChannel.name)
					iCrawl.start()
					crawlDict[iChannel.name] = iCrawl
					
					logger.info("Currently crawling " + str(len(crawlDict)) + " channels")
					if len(crawlDict) == MAX_CURRENT_CRAWLS:
						break
		
		logger.info("sleeping for 2 minutes")
		time.sleep(120)



 

except BaseException as e:

	logger.warning("Exception ocurred, exiting...")
	logger.warning(e)
	traceback.print_exc()
	for name, iCrawl in crawlDict.iteritems():
		logger.warning("Killing " + name)
		iCrawl.stop_bot()

finally:
	for name, iCrawl in crawlDict.iteritems():
		logger.warning("Killing " + name)
		iCrawl.stop_bot()
