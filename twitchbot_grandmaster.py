#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import os
import os.path
import time
import datetime
import urllib2, urllib
import json
from pprint import pprint
from threading import Thread
import logging
import codecs
import traceback

logging.VERBOSE = 5
logging.addLevelName(logging.VERBOSE, "VERBOSE")
logging.Logger.verbose = lambda inst, msg, *args, **kwargs: inst.log(logging.VERBOSE, msg, *args, **kwargs)
logging.verbose = lambda msg, *args, **kwargs: logging.log(logging.VERBOSE, msg, *args, **kwargs)

logger = logging.getLogger("twitch_bot")
logger.setLevel(logging.INFO)

fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(fmt)

logger.addHandler(ch)

class TwitchBot(Thread):

	PASS="oauth:sgt8c7abih2f72ta0mnwd9svzgem47" ##Instead of a password, use this http://twitchapps.com/tmi/
	NICK="roland_deschain_69"
	REALNAME="roland_deschain_69"
	IDENT="roland_deschain_69" ##Bot username again

	def __init__(self, iChannel):
		Thread.__init__(self, None, self.run)
		self.stop = False
		self.channel = iChannel

	def stop_bot(self):
		self.stop = True

	def run(self):

		CHANNEL = "#" + self.channel.name
		GAME = self.channel.game.replace("/","")

		logger.debug("Starting bot...")
		f=""
		try:
			filepath = "./dataset_new/" + codecs.decode(GAME,"utf-8") + "_" + CHANNEL
			if os.path.isfile(filepath):
				f = open(filepath,"a")
			else:
				f = open(filepath,"w")
		except BaseException as e:
			traceback.print_exc()
			logger.warning(e)
			logger.warning("GAME "+ str(GAME))
			logger.warning("CHANNEL " + str(CHANNEL))
			self.stop=True
			exit()

		s = socket.socket()
		host, port = self.channel.get_connection_params()
		try:
			s.connect((host,port))
		except:
			traceback.print_exc()
			logger.warning("cannot connect to " + CHANNEL)
			self.stop=True
			exit()

		s.send("PASS %s\r\n" % self.PASS)
		s.send("NICK %s\r\n" % self.NICK)
		s.send("USER %s %s bla :%s\r\n" % (self.IDENT, host, self.REALNAME))
		s.send("JOIN %s\r\n" % CHANNEL)
	
		logger.debug("Joined " + CHANNEL)
		
		readbuffer = ""
		try:
			s.settimeout(1)
			while not self.stop:
				try:
					readbuffer=readbuffer+s.recv(1024)
					temp=readbuffer.split("\n")
					readbuffer=temp.pop()
					
					for line in temp:					
						toks = line.strip().split()
						if(toks[0]=="PING"):
							s.send("PONG %s\r\n" % line[1])

						if "PRIVMSG" in line:
							ts = time.time()
							timestamp = datetime.datetime.fromtimestamp(ts).strftime(':%Y-%m-%d %H.%M.%S ')
							line = timestamp + line

							logger.verbose(line)

							f.write(line + "\n")
							f.flush()
							os.fsync(f)
		
				except socket.timeout as e:
					err = e.args[0]
					if err != 'timed out':
						raise e


		finally:
			logger.warning("Exiting bot for channel " + CHANNEL)
			s.close()
			if f:
				f.close()



class TwitchChat:

	HOST = "irc.twitch.tv"
	PORT = 6667

	def __init__(self, name, game, viewers):
		self.name = name
		if game:
			self.game = codecs.encode(game,"utf-8")
		else:
			self.game="nogame"
		self.viewers = viewers
		

	def __repr__(self):
		repr_fmt = "Channel <%s, %s, %s>"
		return repr_fmt % (self.name, self.game, self.viewers)
	
	def is_live(self, retry=5):
		url = "https://api.twitch.tv/kraken/streams/"+ self.name
		i = 0
		live = None
		data = ""
		while live is None and i<retry:
			try:
				response = urllib2.urlopen(url)
				data = json.load(response)
				live = "stream" in data and "error" not in data

			except BaseException as e:
				logger.warning(data)
				logger.warning(e)
				logger.warning(url)

			i+=1

		return live

	def get_connection_params(self):
		url = "http://api.twitch.tv/api/channels/"+self.name+"/chat_properties"
		response = urllib2.urlopen(url)
		data = json.load(response)

		if data["eventchat"]:
			pieces = data["chat_servers"][0].split(":")
			connection_params = (pieces[0],int(pieces[1]))
		else:
			connection_params = (TwitchChat.HOST, TwitchChat.PORT)

		return connection_params


	@staticmethod
	def get_live_channels(language, game=None, min_viewers=0, limit=None):
		'''
			Gets the list of current live channels in twitch.
		'''
		url = "https://api.twitch.tv/kraken/streams?broadcaster_language="+language+"&limit=100"
		live_streams = []
		nResults = 1
		while nResults and (not limit or len(live_streams) < limit):
			if game:
				url += "&game="+urllib.quote(game)

			response = urllib2.urlopen(url)

			data = json.load(response)
			nResults = len(data["streams"])

			for channel in data["streams"]:
				if len(live_streams) == limit:
					break

				if channel["viewers"] > min_viewers:
					tchannel = TwitchChat(channel["channel"]["display_name"].lower().replace(" ",""), channel["channel"]["game"], channel["viewers"])
					live_streams.append(tchannel)

			url = data["_links"]["next"]

		return live_streams

class TwitchGame():

	def __init__(self, name, viewers, channels):
		self.name = name
		self.viewers = viewers
		self.channels = channels

	def __repr__(self):
		repr_fmt = "Game <%s, %s, %s>"
		return repr_fmt % (self.name, self.viewers, self.channels)

	@staticmethod
	def get_top_games():
		'''
			Gets the most live streamed games in twitch
		'''
		url = "https://api.twitch.tv/kraken/games/top?limit=100"
		top_games = []
		nResults = 1

		while nResults != 0:
			response = urllib2.urlopen(url)

			data = json.load(response)
			nResults = len(data["top"])

			for game_info in data["top"]:
				elem = TwitchGame(game_info["game"]["name"], game_info["viewers"], game_info["channels"])
				top_games.append(elem)

			url = data["_links"]["next"]
		return top_games


if __name__ == "__main__":

	iTwitch = TwitchBot()
	#print iTwitch.get_live_channels("en", "Starcraft II")
	print iTwitch.get_top_games()