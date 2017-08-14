import urllib2
import json
import os
import MySQLdb

db = MySQLdb.connect("localhost","root","pany8491","Twitch",charset="utf8" )

class TwitchAPI:

	baseUrl = "https://api.twitch.tv/kraken/"

	def __init__(self):
		pass


	def getAuth(self):
		pass


	def getChannelInfo(self, channelName):
		endpoint = "/channels/"+channelName
		url = self.baseUrl+endpoint

		response = urllib2.urlopen(url)
		data = json.load(response)
		return TwitchChannel(data)

	def getChannelFollowers(self, channelName):

		iChannel, idChannel = self.loadChannel(channelName)
		if not iChannel:
			try:
				iChannel = self.getChannelInfo(channelName)
				idChannel = iChannel.insert_channel()
			except urllib2.HTTPError as e:
				print e
				return
			except urllib2.URLError as e:
				print e
				return
			
		endpoint = "/channels/"+channelName+"/follows"
		options = "?direction=ASC&limit=2000&sortby=created_at"
		url = self.baseUrl+endpoint+options
		nResults = 1
		iUsers = TwitchUsers(idChannel)

		while nResults!=0:
			try:
				response = urllib2.urlopen(url)
			except urllib2.URLError as e:
				print e
				return
			except httplib.BadStatusLine as e:
				print e
				return
			data = json.load(response)
			nResults = len(data["follows"])
			for user_info in data["follows"]:
				iUser = TwitchUser(user_info)
				iUsers.add(iUser)

			url = data["_links"]["next"]

		iUsers.insert_bulk()

	def getUserInfo(self, userName):
		endpoint = "/users/"+userName
		url = self.baseUrl+endpoint

		response = urllib2.urlopen(url)
		data = json.load(response)
		return TwitchUser(data)

	#CANVIAR PER FER BULK INSERT
	'''def getUserFollows(self, userName):

		iUser = self.loadUser(userName)
		if not iUser:
			try:
				iUser = self.getUserInfo(userName)
			except urllib2.HTTPError:
				return
		else:
			print "got this"

		idUser = iUser.insert_user()

		endpoint = "/users/"+userName+"/follows/channels"
		options = "?direction=ASC&limit=2000&sortby=created_at"
		url = self.baseUrl+endpoint+options

		nResults = 1
		while nResults!=0:
			response = urllib2.urlopen(url)
			data = json.load(response)
			nResults = len(data["follows"])

			for channel_info in data["follows"]:
				iChannel = TwitchChannel(channel_info)
				idChannel = iChannel.insert_channel()

				follow_date = channel_info["created_at"]
				notifications_active = channel_info["notifications"]
				
				iFollower = TwitchFollower(idUser,idChannel,follow_date,notifications_active)
				iFollower.insert_follower()

			url = data["_links"]["next"]
	'''
	def loadChannel(self, channelName):
		cursor = db.cursor()
		rows_count = cursor.execute("SELECT * FROM Channel WHERE channelname = %s",(channelName))
		columns = [column[0] for column in cursor.description]
		
		iChannel = None
		idChannel = -1

		if rows_count > 0:
			row = cursor.fetchone()
			result = dict(zip(columns, row))
			idChannel = result["id"]
			iChannel = TwitchChannel(result)
		
		cursor.close()
		return iChannel, idChannel

	def loadUser(self, userName):
		cursor = db.cursor()
		rows_count = cursor.execute("SELECT * FROM User WHERE username = %s",(userName))
		columns = [column[0] for column in cursor.description]
		
		iUser = None
		if rows_count > 0:
			row = cursor.fetchone()
			result = dict(zip(columns, row))
			iUser = TwitchUser(result)
		
		return iUser



class TwitchUsers:

	def __init__(self, followedChannel):
		self.users = []
		self.idChannel = followedChannel
		self.inserted_ids = []

	def add(self,user):
		self.users.append(user)

	def insert_bulk(self):
		self.insert_bulk_users()
		self.insert_bulk_followers()

	def insert_bulk_users(self):
		cursor = db.cursor()
		insert_array = []

		for user in self.users:
			rows_count = cursor.execute("SELECT id FROM User WHERE username = %s",(user.username))
			if rows_count == 0:
				elem = (user.created_at,user.user_id,user.logo,user.bio,user.username)
				insert_array.append(elem)

		if len(insert_array) > 0:
			cursor.executemany("INSERT INTO User(created_at,user_id,logo,bio,username) VALUES(%s,%s,%s,%s,%s)",insert_array)	
			lastIdUser = db.insert_id()
			
			self.inserted_ids.insert(0,lastIdUser)
			nUsers = len(insert_array)
			currentId = lastIdUser - 1

			while currentId > lastIdUser - nUsers:
				self.inserted_ids.insert(0,currentId)
				currentId -=1

			db.commit()

		cursor.close()
		
	def insert_bulk_followers(self):

		cursor = db.cursor()
		insert_followers = []

		for user_id in self.inserted_ids:
			rows_count = cursor.execute("SELECT id FROM Follower WHERE user = %s AND channel= %s",(user_id, self.idChannel))
			if rows_count == 0:
				elem = (user_id, self.idChannel)
				insert_followers.append(elem)

		if len(insert_followers) > 0:
			cursor.executemany("INSERT INTO Follower(user, channel) VALUES(%s,%s)",insert_followers)	
			db.commit()	

		cursor.close()


class TwitchUser:

	def __init__(self, user_info):
		
		if "user" in user_info:
			us = user_info["user"]
		else:
			us = user_info

		self.created_at = us["created_at"]
		if "_id" in us:
			self.user_id = us["_id"]
		else:
			self.user_id = us["user_id"]
		
		if "display_name" in us:
			self.username = us["display_name"].lower()
		else:
			self.username = us["username"]

		self.bio = us["bio"]
		self.logo = us["logo"]

	def __repr__(self):
		return str(self.user_id) + " " +str(self.username) + " " + str(self.created_at) + " " + str(self.bio) + " " + str(self.logo)

	

class TwitchChannel:

	def __init__(self, channel_info):
		if "channel" in channel_info:
			ch = channel_info["channel"]
		else:
			ch = channel_info

		if "_id" in ch:
			self.channel_id = ch["_id"]
		else:
			self.channel_id = ch["channel_id"]

		self.logo = ch["logo"]
		self.mature = ch["mature"]

		if "display_name" in ch:
			self.channelname = ch["display_name"].lower()
		else:
			self.channelname = ch["channelname"]

		self.created_at = ch["created_at"]
		self.followers = ch["followers"]
		self.views = ch["views"]
		self.language = ch["language"]
		self.video_banner = ch["video_banner"]
		self.profile_banner = ch["profile_banner"]
		
		if "profile_banner_background_color" in ch:
			self.profile_banner_background_color = ch["profile_banner_background_color"]
		else:
			self.profile_banner_background_color = ch["profile_banner_bc"]
		
		self.banner = ch["banner"]
		self.background = ch["background"]

	def insert_channel(self):
		cursor = db.cursor()
		rows_count = cursor.execute("SELECT id FROM Channel WHERE channelname = %s",(self.channelname))
			
		if rows_count > 0:
			tuples = cursor.fetchall()
			idChannel = tuples[0][0]
		else:
			try:
				cursor.execute('''INSERT INTO Channel(channel_id,channelname,logo,mature,created_at,followers,views,language,video_banner,profile_banner,profile_banner_bc,banner,background) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (self.channel_id,self.channelname,self.logo,self.mature,self.created_at,self.followers,self.views, self.language,self.video_banner,self.profile_banner,self.profile_banner_background_color,self.banner,self.background))
				idChannel = db.insert_id()
				db.commit()

			finally:
				cursor.close()

		cursor.close()
		return idChannel


if __name__ == '__main__':
	iTwitchApi = TwitchAPI()
	for fname in os.listdir("./dataset/"):
		channelName = fname.split("_#")[1]
		iTwitchApi.getChannelFollowers(channelName)
