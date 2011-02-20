#!/usr/bin/python2.4
#
# Copyright 2007 The Python-Twitter Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
A library that provides a Python interface to the Twitter API


Changes/Updates:
- Added support for next_page/prev_page pagination items.  It was missing from some calls.
- Changed functions to be names normal camel humps instead of camel humps extreme.
- Fixed FileCache class so that it actually works.
- Added the ability to override caching on a call-by-call basis in a standard way.
'''

__author__ = 'outtatime@gmail.com'
__version__ = '0.9.0'


import base64
import calendar
import datetime
import httplib
import os
import rfc822
import sys
import tempfile
import textwrap
import time
import calendar
import urllib
import urllib2
import socket
import urlparse
import gzip
import StringIO
import re

# Tor!
#import socks
#import socket
#socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, '127.0.0.1', 9050)
#socket.socket = socks.socksocket


# For multipart formdata uploading.
#from poster.encode import multipart_encode
#from poster.streaminghttp import register_openers

#from wget import wget, wget_opener

try:
  # Python >= 2.6
  import json as simplejson
except ImportError:
  try:
    # Python < 2.6
    import simplejson
  except ImportError:
    try:
      # Google App Engine
      from django.utils import simplejson
    except ImportError:
      raise ImportError, "Unable to load a json library"

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl, parse_qs
except ImportError:
  from cgi import parse_qsl, parse_qs

try:
  from hashlib import md5
except ImportError:
  from md5 import md5

import oauth2 as oauth


SOCKET_TIMEOUT = 15

socket.setdefaulttimeout(SOCKET_TIMEOUT)

CHARACTER_LIMIT = 140

# A singleton representing a lazily instantiated FileCache.
DEFAULT_CACHE = object()

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'


class TwitterError(Exception):
    '''Base class for Twitter errors'''

    @property
    def message(self):
        '''Returns the first argument used to construct this error.'''
        return self.args[0]


class Status(object):
    '''A class representing the Status structure used by the twitter API.

    The Status structure exposes the following properties:

        status.created_at
        status.created_at_in_seconds # read only
        status.favorited
        status.in_reply_to_screen_name
        status.in_reply_to_user_id
        status.in_reply_to_status_id
        status.truncated
        status.source
        status.id
        status.text
        status.location
        status.relative_created_at # read only
        status.user
        status.urls
        status.user_mentions
        status.hashtags
        status.geo
        status.place
        status.coordinates
        status.contributors
        status.retweeted
        status.retweeted_status
    '''
    def __init__(self,
        created_at=None,
        favorited=None,
        id=None,
        text=None,
        location=None,
        user=None,
        in_reply_to_screen_name=None,
        in_reply_to_user_id=None,
        in_reply_to_status_id=None,
        truncated=None,
        source=None,
        now=None,
        urls=None,
        user_mentions=None,
        hashtags=None,
        geo=None,
        place=None,
        coordinates=None,
        contributors=None,
        retweeted=None,
        retweeted_status=None):
        '''
        An object to hold a Twitter status message.

        This class is normally instantiated by the twitter.Api class and
        returned in a sequence.

        Note: Dates are posted in the form "Sat Jan 27 04:17:38 +0000 2007"

        Args:
            created_at:
                The time this status message was posted. [Optional]
            favorited:
                Whether this is a favorite of the authenticated user. [Optional]
            id:
                The unique id of this status message. [Optional]
            text:
                The text of this status message. [Optional]
            location:
                the geolocation string associated with this message. [Optional]
            relative_created_at:
                A human readable string representing the posting time. [Optional]
            user:
                A twitter.User instance representing the person posting the
                message. [Optional]
            now:
                The current time, if the client choses to set it.
                Defaults to the wall clock time. [Optional]
            urls:
                -description
            user_mentions:
                -description
            hashtags:
                -description
            geo:
                -description
            place:
                -description
            coordinates:
                -description
            contributors:
                -description
            retweeted:
                -description
            retweeted_status:
                Feb 2011 - Twitter now supports "retweeted_status" field in
                "Status" objects.
                With this support, it becomes possible to retrieve full text of
                a retweeted message, even if it is longer than 140 characters in
                legacy "text" field.
        '''
        self.created_at = created_at
        self.favorited = favorited
        self.id = id
        self.text = text
        self.location = location
        self.user = user
        self.now = now
        self.in_reply_to_screen_name = in_reply_to_screen_name
        self.in_reply_to_user_id = in_reply_to_user_id
        self.in_reply_to_status_id = in_reply_to_status_id
        self.truncated = truncated
        self.retweeted = retweeted
        self.source = source
        self.urls = urls
        self.user_mentions = user_mentions
        self.hashtags = hashtags
        self.geo = geo
        self.place = place
        self.coordinates = coordinates
        self.contributors = contributors
        self.retweeted_status = retweeted_status

    def getCreatedAt(self):
        '''
        Get the time this status message was posted.

        Returns:
            The time this status message was posted
        '''
        return self._created_at

    def setCreatedAt(self, created_at):
        '''
        Set the time this status message was posted.

        Args:
            created_at:
                The time this status message was created
        '''
        self._created_at = created_at

    created_at = property(getCreatedAt, setCreatedAt,
        doc='The time this status message was posted.')

    def getCreatedAtInSeconds(self):
        '''
        Get the time this status message was posted, in seconds since the epoch.

        Returns:
            The time this status message was posted, in seconds since the epoch.
        '''
        return calendar.timegm(rfc822.parsedate(self.created_at))

    created_at_in_seconds = property(getCreatedAtInSeconds,
        doc="The time this status message was posted, in seconds since the epoch")

    def getFavorited(self):
        '''
        Get the favorited setting of this status message.

        Returns:
            True if this status message is favorited; False otherwise
        '''
        return self._favorited

    def setFavorited(self, favorited):
        '''
        Set the favorited state of this status message.

        Args:
            favorited:
                boolean True/False favorited state of this status message
        '''
        self._favorited = favorited

    favorited = property(getFavorited, setFavorited,
        doc='The favorited state of this status message.')

    def getId(self):
        '''
        Get the unique id of this status message.

        Returns:
            The unique id of this status message
        '''
        return self._id

    def setId(self, id):
        '''
        Set the unique id of this status message.

        Args:
            id:
                The unique id of this status message
        '''
        self._id = id

    id = property(getId, setId, doc='The unique id of this status message.')

    def getInReplyToScreenName(self):
        return self._in_reply_to_screen_name

    def setInReplyToScreenName(self, in_reply_to_screen_name):
        self._in_reply_to_screen_name = in_reply_to_screen_name

    in_reply_to_screen_name = property(getInReplyToScreenName,
        setInReplyToScreenName, doc='')

    def getInReplyToUserId(self):
        return self._in_reply_to_user_id

    def setInReplyToUserId(self, in_reply_to_user_id):
        self._in_reply_to_user_id = in_reply_to_user_id

    in_reply_to_user_id = property(getInReplyToUserId,
        setInReplyToUserId, doc='')

    def getInReplyToStatusId(self):
        return self._in_reply_to_status_id

    def setInReplyToStatusId(self, in_reply_to_status_id):
        self._in_reply_to_status_id = in_reply_to_status_id

    in_reply_to_status_id = property(getInReplyToStatusId,
        setInReplyToStatusId, doc='')

    def getTruncated(self):
        return self._truncated

    def setTruncated(self, truncated):
        self._truncated = truncated

    truncated = property(getTruncated, setTruncated, doc='')

    def getRetweeted(self):
        return self._retweeted

    def setRetweeted(self, retweeted):
        self._retweeted = retweeted

    retweeted = property(getRetweeted, setRetweeted, doc='')

    def getSource(self):
        return self._source

    def setSource(self, source):
        self._source = source

    source = property(getSource, setSource, doc='')

    def getText(self):
        '''
        Get the text of this status message.

        Returns:
            The text of this status message.
        '''
        return self._text

    def setText(self, text):
        '''
        Set the text of this status message.

        Args:
            text:
                The text of this status message
        '''
        self._text = text

    text = property(getText, setText,
        doc='The text of this status message')

    def getLocation(self):
        '''
        Get the geolocation associated with this status message

        Returns:
            The geolocation string of this status message.
        '''
        return self._location

    def setLocation(self, location):
        '''
        Set the geolocation associated with this status message

        Args:
            location:
                The geolocation string of this status message
        '''
        self._location = location

    location = property(getLocation, setLocation,
        doc='The geolocation string of this status message')

    def getRelativeCreatedAt(self):
        '''
        Get a human redable string representing the posting time

        Returns:
            A human readable string representing the posting time
        '''
        fudge = 1.25
        delta  = long(self.now) - long(self.created_at_in_seconds)
        if delta < (1 * fudge):
            return 'about a second ago'
        elif delta < (60 * (1/fudge)):
            return 'about %d seconds ago' % (delta)
        elif delta < (60 * fudge):
            return 'about a minute ago'
        elif delta < (60 * 60 * (1/fudge)):
            return 'about %d minutes ago' % (delta / 60)
        elif delta < (60 * 60 * fudge) or delta / (60 * 60) == 1:
            return 'about an hour ago'
        elif delta < (60 * 60 * 24 * (1/fudge)):
            return 'about %d hours ago' % (delta / (60 * 60))
        elif delta < (60 * 60 * 24 * fudge) or delta / (60 * 60 * 24) == 1:
            return 'about a day ago'
        else:
            return 'about %d days ago' % (delta / (60 * 60 * 24))

    relative_created_at = property(getRelativeCreatedAt,
        doc='Get a human readable string representing the posting time')

    def getUser(self):
        '''
        Get a twitter.User reprenting the entity posting this status message.

        Returns:
            A twitter.User reprenting the entity posting this status message
        '''
        return self._user

    def setUser(self, user):
        '''
        Set a twitter.User reprenting the entity posting this status message.

        Args:
            user:
                A twitter.User reprenting the entity posting this status message
        '''
        self._user = user

    user = property(getUser, setUser,
        doc='A twitter.User reprenting the entity posting this status message')

    def getNow(self):
        '''
        Get the wallclock time for this status message.

        Used to calculate relative_created_at.  Defaults to the time
        the object was instantiated.

        Returns:
            Whatever the status instance believes the current time to be,
            in seconds since the epoch.
        '''
        if self._now is None:
            self._now = time.time()
        return self._now

    def setNow(self, now):
        '''
        Set the wallclock time for this status message.

        Used to calculate relative_created_at.  Defaults to the time
        the object was instantiated.

        Args:
            now:
                The wallclock time for this instance.
        '''
        self._now = now

    now = property(getNow, setNow, doc='The wallclock time for this status instance.')

    def getGeo(self):
        return self._geo

    def setGeo(self, geo):
        self._geo = geo

    geo = property(getGeo, setGeo, doc='')

    def getPlace(self):
        return self._place

    def setPlace(self, place):
        self._place = place

    place = property(getPlace, setPlace, doc='')

    def getCoordinates(self):
        return self._coordinates

    def setCoordinates(self, coordinates):
        self._coordinates = coordinates

    coordinates = property(getCoordinates, setCoordinates, doc='')

    def getContributors(self):
        return self._contributors

    def setContributors(self, contributors):
        self._contributors = contributors

    contributors = property(getContributors, setContributors, doc='')

    def getRetweetedStatus(self):
        return self._retweeted_status

    def setRetweetedStatus(self, retweeted_status):
        self._retweeted_status = retweeted_status

    retweeted_status = property(getRetweetedStatus, setRetweetedStatus,
        doc='')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        try:
            return other and \
                self.created_at == other.created_at and \
                self.id == other.id and \
                self.text == other.text and \
                self.location == other.location and \
                self.user == other.user and \
                self.in_reply_to_screen_name == other.in_reply_to_screen_name and \
                self.in_reply_to_user_id == other.in_reply_to_user_id and \
                self.in_reply_to_status_id == other.in_reply_to_status_id and \
                self.truncated == other.truncated and \
                self.retweeted == other.retweeted and \
                self.favorited == other.favorited and \
                self.source == other.source and \
                self.geo == other.geo and \
                self.place == other.place and \
                self.coordinates == other.coordinates and \
                self.contributors == other.contributors and \
                self.retweeted_status == other.retweeted_status
        except AttributeError:
            return False

    def __str__(self):
        '''
        A string representation of this twitter.Status instance.

        The return value is the same as the JSON string representation.

        Returns:
            A string representation of this twitter.Status instance.
        '''
        return self.asJsonString()

    def asJsonString(self):
        '''
        A JSON string representation of this twitter.Status instance.

        Returns:
            A JSON string representation of this twitter.Status instance
        '''
        return simplejson.dumps(self.asDict(), sort_keys=True)

    def asDict(self):
        '''
        A dict representation of this twitter.Status instance.

        The return value uses the same key names as the JSON representation.

        Return:
            A dict representing this twitter.Status instance
        '''
        data = {}
        if self.created_at:
            data['created_at'] = self.created_at
        if self.favorited:
            data['favorited'] = self.favorited
        if self.id:
            data['id'] = self.id
        if self.text:
            data['text'] = self.text
        if self.location:
            data['location'] = self.location
        if self.user:
            data['user'] = self.user.asDict()
        if self.in_reply_to_screen_name:
            data['in_reply_to_screen_name'] = self.in_reply_to_screen_name
        if self.in_reply_to_user_id:
            data['in_reply_to_user_id'] = self.in_reply_to_user_id
        if self.in_reply_to_status_id:
            data['in_reply_to_status_id'] = self.in_reply_to_status_id
        if self.truncated is not None:
            data['truncated'] = self.truncated
        if self.retweeted is not None:
            data['retweeted'] = self.retweeted
        if self.favorited is not None:
            data['favorited'] = self.favorited
        if self.source:
            data['source'] = self.source
        if self.geo:
            data['geo'] = self.geo
        if self.place:
            data['place'] = self.place
        if self.coordinates:
            data['coordinates'] = self.coordinates
        if self.contributors:
            data['contributors'] = self.contributors
        if self.hashtags:
            data['hashtags'] = [h.text for h in self.hashtags]
        if self.retweeted_status:
            data['retweeted_status'] = self.retweeted_status.AsDict()
        return data

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data: A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.Status instance
        '''
        if 'user' in data:
            user = User.newFromJsonDict(data['user'])
        else:
            user = None
        urls = None
        user_mentions = None
        hashtags = None
        if 'retweeted_status' in data:
            retweeted_status = Status.newFromJsonDict(data['retweeted_status'])
        else:
            retweeted_status = None
        if 'entities' in data:
            if 'urls' in data['entities']:
                urls = [Url.newFromJsonDict(u) for u in data['entities']['urls']]
            if 'user_mentions' in data['entities']:
                user_mentions = [User.newFromJsonDict(u) for u in data['entities']['user_mentions']]
            if 'hashtags' in data['entities']:
                hashtags = [Hashtag.newFromJsonDict(h) for h in data['entities']['hashtags']]
        return Status(created_at=data.get('created_at', None),
            favorited=data.get('favorited', None),
            id=data.get('id', None),
            text=data.get('text', None),
            location=data.get('location', None),
            in_reply_to_screen_name=data.get('in_reply_to_screen_name', None),
            in_reply_to_user_id=data.get('in_reply_to_user_id', None),
            in_reply_to_status_id=data.get('in_reply_to_status_id', None),
            truncated=data.get('truncated', None),
            retweeted=data.get('retweeted', None),
            source=data.get('source', None),
            user=user,
            urls=urls,
            user_mentions=user_mentions,
            hashtags=hashtags,
            geo=data.get('geo', None),
            place=data.get('place', None),
            coordinates=data.get('coordinates', None),
            contributors=data.get('contributors', None),
            retweeted_status=retweeted_status)


class User(object):
    '''
    A class representing the User structure used by the twitter API.

    The User structure exposes the following properties:

        user.id
        user.name
        user.screen_name
        user.location
        user.description
        user.profile_image_url
        user.profile_background_tile
        user.profile_background_image_url
        user.profile_sidebar_fill_color
        user.profile_background_color
        user.profile_link_color
        user.profile_text_color
        user.protected
        user.utc_offset
        user.time_zone
        user.url
        user.status
        user.statuses_count
        user.followers_count
        user.friends_count
        user.favourites_count
        user.geo_enabled
    '''
    def __init__(self,
        id=None,
        name=None,
        screen_name=None,
        location=None,
        description=None,
        profile_image_url=None,
        profile_background_tile=None,
        profile_background_image_url=None,
        profile_sidebar_fill_color=None,
        profile_background_color=None,
        profile_link_color=None,
        profile_text_color=None,
        protected=None,
        utc_offset=None,
        time_zone=None,
        followers_count=None,
        friends_count=None,
        statuses_count=None,
        favourites_count=None,
        url=None,
        status=None,
        geo_enabled=None):
        self.id = id
        self.name = name
        self.screen_name = screen_name
        self.location = location
        self.description = description
        self.profile_image_url = profile_image_url
        self.profile_background_tile = profile_background_tile
        self.profile_background_image_url = profile_background_image_url
        self.profile_sidebar_fill_color = profile_sidebar_fill_color
        self.profile_background_color = profile_background_color
        self.profile_link_color = profile_link_color
        self.profile_text_color = profile_text_color
        self.protected = protected
        self.utc_offset = utc_offset
        self.time_zone = time_zone
        self.followers_count = followers_count
        self.friends_count = friends_count
        self.statuses_count = statuses_count
        self.favourites_count = favourites_count
        self.url = url
        self.status = status
        self.geo_enabled = geo_enabled

    def getId(self):
        '''
        Get the unique id of this user.

        Returns:
            The unique id of this user
        '''
        return self._id

    def setId(self, id):
        '''
        Set the unique id of this user.

        Args:
            id:
                The unique id of this user.
        '''
        self._id = id

    id = property(getId, setId,
        doc='The unique id of this user.')

    def getName(self):
        '''
        Get the real name of this user.

        Returns:
            The real name of this user
        '''
        return self._name

    def setName(self, name):
        '''
        Set the real name of this user.

        Args:
        name: The real name of this user
        '''
        self._name = name

    name = property(getName, setName,
        doc='The real name of this user.')

    def getScreenName(self):
        '''
        Get the short twitter name of this user.

        Returns:
            The short twitter name of this user
        '''
        return self._screen_name

    def setScreenName(self, screen_name):
        '''
        Set the short twitter name of this user.

        Args:
        screen_name: the short twitter name of this user
        '''
        self._screen_name = screen_name

    screen_name = property(getScreenName, setScreenName,
        doc='The short twitter name of this user.')

    def getLocation(self):
        '''
        Get the geographic location of this user.

        Returns:
            The geographic location of this user
        '''
        return self._location

    def setLocation(self, location):
        '''
        Set the geographic location of this user.

        Args:
        location: The geographic location of this user
        '''
        self._location = location

    location = property(getLocation, setLocation,
        doc='The geographic location of this user.')

    def getDescription(self):
        '''
        Get the short text description of this user.

        Returns:
        The short text description of this user
        '''
        return self._description

    def setDescription(self, description):
        '''
        Set the short text description of this user.

        Args:
            description: The short text description of this user
        '''
        self._description = description

    description = property(getDescription, setDescription,
        doc='The short text description of this user.')

    def getUrl(self):
        '''
        Get the homepage url of this user.

        Returns:
            The homepage url of this user
        '''
        return self._url

    def setUrl(self, url):
        '''
        Set the homepage url of this user.

        Args:
            url: The homepage url of this user
        '''
        self._url = url

    url = property(getUrl, setUrl,
        doc='The homepage url of this user.')

    def getProfileImageUrl(self):
        '''
        Get the url of the thumbnail of this user.

        Returns:
            The url of the thumbnail of this user
        '''
        return self._profile_image_url

    def setProfileImageUrl(self, profile_image_url):
        '''
        Set the url of the thumbnail of this user.

        Args:
            profile_image_url: The url of the thumbnail of this user
        '''
        self._profile_image_url = profile_image_url

    profile_image_url= property(getProfileImageUrl, setProfileImageUrl,
        doc='The url of the thumbnail of this user.')

    def getProfileBackgroundTile(self):
        '''
        Boolean for whether to tile the profile background image.

        Returns:
            True if the background is to be tiled, False if not, None if unset.
        '''
        return self._profile_background_tile

    def setProfileBackgroundTile(self, profile_background_tile):
        '''
        Set the boolean flag for whether to tile the profile background image.

        Args:
            profile_background_tile: Boolean flag for whether to tile or not.
        '''
        self._profile_background_tile = profile_background_tile

    profile_background_tile = property(getProfileBackgroundTile, setProfileBackgroundTile,
        doc='Boolean for whether to tile the background image.')

    def getProfileBackgroundImageUrl(self):
        return self._profile_background_image_url

    def setProfileBackgroundImageUrl(self, profile_background_image_url):
        self._profile_background_image_url = profile_background_image_url

    profile_background_image_url = property(getProfileBackgroundImageUrl, setProfileBackgroundImageUrl,
        doc='The url of the profile background of this user.')

    def getProfileSidebarFillColor(self):
        return self._profile_sidebar_fill_color

    def setProfileSidebarFillColor(self, profile_sidebar_fill_color):
        self._profile_sidebar_fill_color = profile_sidebar_fill_color

    profile_sidebar_fill_color = property(getProfileSidebarFillColor, setProfileSidebarFillColor)

    def getProfileBackgroundColor(self):
        return self._profile_background_color

    def setProfileBackgroundColor(self, profile_background_color):
        self._profile_background_color = profile_background_color

    profile_background_color = property(getProfileBackgroundColor, setProfileBackgroundColor)

    def getProfileLinkColor(self):
        return self._profile_link_color

    def setProfileLinkColor(self, profile_link_color):
        self._profile_link_color = profile_link_color

    profile_link_color = property(getProfileLinkColor, setProfileLinkColor)

    def getProfileTextColor(self):
        return self._profile_text_color

    def setProfileTextColor(self, profile_text_color):
        self._profile_text_color = profile_text_color

    profile_text_color = property(getProfileTextColor, setProfileTextColor)

    def getProtected(self):
        return self._protected

    def setProtected(self, protected):
        self._protected = protected

    protected = property(getProtected, setProtected)

    def getUtcOffset(self):
        return self._utc_offset

    def setUtcOffset(self, utc_offset):
        self._utc_offset = utc_offset

    utc_offset = property(getUtcOffset, setUtcOffset)

    def getTimeZone(self):
        '''
        Gets the current time zone string for the user.

        Returns:
            The descriptive time zone string for the user.
        '''
        return self._time_zone

    def setTimeZone(self, time_zone):
        '''
        Sets the user's time zone string.

        Args:
            time_zone:
                The descriptive time zone to assign for the user.
        '''
        self._time_zone = time_zone

    time_zone = property(getTimeZone, setTimeZone)

    def getStatus(self):
        '''
        Get the latest twitter.Status of this user.

        Returns:
            The latest twitter.Status of this user
        '''
        return self._status

    def setStatus(self, status):
        '''
        Set the latest twitter.Status of this user.

        Args:
            status:
                The latest twitter.Status of this user
        '''
        self._status = status

    status = property(getStatus, setStatus,
        doc='The latest twitter.Status of this user.')

    def getFriendsCount(self):
        '''
        Get the friend count for this user.

        Returns:
            The number of users this user has befriended.
        '''
        return self._friends_count

    def setFriendsCount(self, count):
        '''
        Set the friend count for this user.

        Args:
            count:
                The number of users this user has befriended.
        '''
        self._friends_count = count

        friends_count = property(getFriendsCount, setFriendsCount,
            doc='The number of friends for this user.')

    def getFollowersCount(self):
        '''
        Get the follower count for this user.

        Returns:
            The number of users following this user.
        '''
        return self._followers_count

    def setFollowersCount(self, count):
        '''
        Set the follower count for this user.

        Args:
            count:
            The number of users following this user.
        '''
        self._followers_count = count

    followers_count = property(getFollowersCount, setFollowersCount,
        doc='The number of users following this user.')

    def getStatusesCount(self):
        '''
        Get the number of status updates for this user.

        Returns:
            The number of status updates for this user.
            '''
        return self._statuses_count

    def setStatusesCount(self, count):
        '''
        Set the status update count for this user.

        Args:
            count:
                The number of updates for this user.
        '''
        self._statuses_count = count

    statuses_count = property(getStatusesCount, setStatusesCount,
        doc='The number of updates for this user.')

    def getFavouritesCount(self):
        '''
        Get the number of favourites for this user.

        Returns:
            The number of favourites for this user.
        '''
        return self._favourites_count

    def setFavouritesCount(self, count):
        '''
        Set the favourite count for this user.

        Args:
            count:
                The number of favourites for this user.
        '''
        self._favourites_count = count

    favourites_count = property(getFavouritesCount, setFavouritesCount,
        doc='The number of favourites for this user.')

    def getGeoEnabled(self):
        '''
        Get the setting of geo_enabled for this user.

        Returns:
            True/False if Geo tagging is enabled
        '''
        return self._geo_enabled

    def setGeoEnabled(self, geo_enabled):
        '''
        Set the latest twitter.geo_enabled of this user.

        Args:
            geo_enabled:
                True/False if Geo tagging is to be enabled
        '''
        self._geo_enabled = geo_enabled

    geo_enabled = property(getGeoEnabled, setGeoEnabled,
        doc='The value of twitter.geo_enabled for this user.')

    def __ne__(self, other):
        return not self.__eq__(other)

    '''
    Set this to False to enable looser equality checking (Cached vs. uncached
    users can have varying numbers of followers, which would make the objects
    appear to be not equal when in fact we may only care about the screen_name
    or id being identical).
    '''
    strict_equality = True

    def __eq__(self, other):
        try:
            if not self.strict_equality:
                return other and self.id == other.id
            return other and \
                self.id == other.id and \
                self.name == other.name and \
                self.screen_name == other.screen_name and \
                self.location == other.location and \
                self.description == other.description and \
                self.profile_image_url == other.profile_image_url and \
                self.profile_background_tile == other.profile_background_tile and \
                self.profile_background_image_url == other.profile_background_image_url and \
                self.profile_sidebar_fill_color == other.profile_sidebar_fill_color and \
                self.profile_background_color == other.profile_background_color and \
                self.profile_link_color == other.profile_link_color and \
                self.profile_text_color == other.profile_text_color and \
                self.protected == other.protected and \
                self.utc_offset == other.utc_offset and \
                self.time_zone == other.time_zone and \
                self.url == other.url and \
                self.statuses_count == other.statuses_count and \
                self.followers_count == other.followers_count and \
                self.favourites_count == other.favourites_count and \
                self.friends_count == other.friends_count and \
                self.status == other.status and \
                self.geo_enabled == other.geo_enabled
        except AttributeError:
            return False

    def __str__(self):
        '''
        A string representation of this twitter.User instance.

        The return value is the same as the JSON string representation.

        Returns:
            A string representation of this twitter.User instance.
        '''
        return self.asJsonString()

    def asJsonString(self):
        '''
        A JSON string representation of this twitter.User instance.

        Returns:
            A JSON string representation of this twitter.User instance.
        '''
        return simplejson.dumps(self.asDict(), sort_keys=True)

    def asDict(self):
        '''
        A dict representation of this twitter.User instance.

        The return value uses the same key names as the JSON representation.

        Return:
            A dict representing this twitter.User instance.
        '''
        data = {}
        if self.id:
            data['id'] = self.id
        if self.name:
            data['name'] = self.name
        if self.screen_name:
            data['screen_name'] = self.screen_name
        if self.location:
            data['location'] = self.location
        if self.description:
            data['description'] = self.description
        if self.profile_image_url:
            data['profile_image_url'] = self.profile_image_url
        if self.profile_background_tile is not None:
            data['profile_background_tile'] = self.profile_background_tile
        if self.profile_background_image_url:
            data['profile_sidebar_fill_color'] = self.profile_background_image_url
        if self.profile_background_color:
            data['profile_background_color'] = self.profile_background_color
        if self.profile_link_color:
            data['profile_link_color'] = self.profile_link_color
        if self.profile_text_color:
            data['profile_text_color'] = self.profile_text_color
        if self.protected is not None:
            data['protected'] = self.protected
        if self.utc_offset:
            data['utc_offset'] = self.utc_offset
        if self.time_zone:
            data['time_zone'] = self.time_zone
        if self.url:
            data['url'] = self.url
        if self.status:
            data['status'] = self.status.asDict()
        if self.friends_count:
            data['friends_count'] = self.friends_count
        if self.followers_count:
            data['followers_count'] = self.followers_count
        if self.statuses_count:
            data['statuses_count'] = self.statuses_count
        if self.favourites_count:
            data['favourites_count'] = self.favourites_count
        if self.geo_enabled:
            data['geo_enabled'] = self.geo_enabled
        return data

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data:
                A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.User instance
        '''
        if 'status' in data:
            status = Status.newFromJsonDict(data['status'])
        else:
            status = None
        return User(id=data.get('id', None),
            name=data.get('name', None),
            screen_name=data.get('screen_name', None),
            location=data.get('location', None),
            description=data.get('description', None),
            statuses_count=data.get('statuses_count', None),
            followers_count=data.get('followers_count', None),
            favourites_count=data.get('favourites_count', None),
            friends_count=data.get('friends_count', None),
            profile_image_url=data.get('profile_image_url', None),
            profile_background_tile = data.get('profile_background_tile', None),
            profile_background_image_url = data.get('profile_background_image_url', None),
            profile_sidebar_fill_color = data.get('profile_sidebar_fill_color', None),
            profile_background_color = data.get('profile_background_color', None),
            profile_link_color = data.get('profile_link_color', None),
            profile_text_color = data.get('profile_text_color', None),
            protected = data.get('protected', None),
            utc_offset = data.get('utc_offset', None),
            time_zone = data.get('time_zone', None),
            url=data.get('url', None),
            status=status,
            geo_enabled=data.get('geo_enabled', None))


class List(object):
    '''
    A class representing the List structure used by the twitter API.

    The List structure exposes the following properties:

        list.id
        list.name
        list.slug
        list.description
        list.full_name
        list.mode
        list.uri
        list.member_count
        list.subscriber_count
        list.following
    '''
    def __init__(self,
        id=None,
        name=None,
        slug=None,
        description=None,
        full_name=None,
        mode=None,
        uri=None,
        member_count=None,
        subscriber_count=None,
        following=None,
        user=None):
        self.id = id
        self.name = name
        self.slug = slug
        self.description = description
        self.full_name = full_name
        self.mode = mode
        self.uri = uri
        self.member_count = member_count
        self.subscriber_count = subscriber_count
        self.following = following
        self.user = user

    def getId(self):
        '''
        Get the unique id of this list.

        Returns:
            The unique id of this list
        '''
        return self._id

    def setId(self, id):
        '''
        Set the unique id of this list.

        Args:
            id:
                The unique id of this list.
        '''
        self._id = id

    id = property(getId, setId,
        doc='The unique id of this list.')

    def getName(self):
        '''
        Get the real name of this list.

        Returns:
            The real name of this list
        '''
        return self._name

    def setName(self, name):
        '''
        Set the real name of this list.

        Args:
            name:
                The real name of this list
        '''
        self._name = name

    name = property(getName, setName,
        doc='The real name of this list.')

    def getSlug(self):
        '''
        Get the slug of this list.

        Returns:
            The slug of this list
        '''
        return self._slug

    def setSlug(self, slug):
        '''
        Set the slug of this list.

        Args:
            slug:
                The slug of this list.
        '''
        self._slug = slug

    slug = property(getSlug, setSlug,
        doc='The slug of this list.')

    def getDescription(self):
        '''
        Get the description of this list.

        Returns:
            The description of this list
            '''
        return self._description

    def setDescription(self, description):
        '''
        Set the description of this list.

        Args:
            description:
                The description of this list.
        '''
        self._description = description

    description = property(getDescription, setDescription,
        doc='The description of this list.')

    def getFull_name(self):
        '''
        Get the full_name of this list.

        Returns:
            The full_name of this list
        '''
        return self._full_name

    def setFull_name(self, full_name):
        '''
        Set the full_name of this list.

        Args:
            full_name:
                The full_name of this list.
        '''
        self._full_name = full_name

    full_name = property(getFull_name, setFull_name,
        doc='The full_name of this list.')

    def getMode(self):
        '''
        Get the mode of this list.

        Returns:
            The mode of this list
        '''
        return self._mode

    def setMode(self, mode):
        '''
        Set the mode of this list.

        Args:
            mode:
                The mode of this list.
        '''
        self._mode = mode

    mode = property(getMode, setMode,
        doc='The mode of this list.')

    def getUri(self):
        '''
        Get the uri of this list.

        Returns:
            The uri of this list
        '''
        return self._uri

    def setUri(self, uri):
        '''
        Set the uri of this list.

        Args:
            uri:
                The uri of this list.
        '''
        self._uri = uri

    uri = property(getUri, setUri, doc='The uri of this list.')

    def getMember_count(self):
        '''
        Get the member_count of this list.

        Returns:
            The member_count of this list
        '''
        return self._member_count

    def setMember_count(self, member_count):
        '''
        Set the member_count of this list.

        Args:
            member_count:
                The member_count of this list.
        '''
        self._member_count = member_count

    member_count = property(getMember_count, setMember_count,
        doc='The member_count of this list.')

    def getSubscriber_count(self):
        '''
        Get the subscriber_count of this list.

        Returns:
            The subscriber_count of this list
        '''
        return self._subscriber_count

    def setSubscriber_count(self, subscriber_count):
        '''
        Set the subscriber_count of this list.

        Args:
            subscriber_count:
                The subscriber_count of this list.
        '''
        self._subscriber_count = subscriber_count

    subscriber_count = property(getSubscriber_count, setSubscriber_count,
        doc='The subscriber_count of this list.')

    def getFollowing(self):
        '''
        Get the following status of this list.

        Returns:
            The following status of this list
        '''
        return self._following

    def setFollowing(self, following):
        '''
        Set the following status of this list.

        Args:
            following:
                The following of this list.
        '''
        self._following = following

    following = property(getFollowing, setFollowing,
        doc='The following status of this list.')

    def getUser(self):
        '''
        Get the user of this list.

        Returns:
            The owner of this list
        '''
        return self._user

    def setUser(self, user):
        '''
        Set the user of this list.

        Args:
            user:
                The owner of this list.
        '''
        self._user = user

    user = property(getUser, setUser, doc='The owner of this list.')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        try:
            return other and \
                self.id == other.id and \
                self.name == other.name and \
                self.slug == other.slug and \
                self.description == other.description and \
                self.full_name == other.full_name and \
                self.mode == other.mode and \
                self.uri == other.uri and \
                self.member_count == other.member_count and \
                self.subscriber_count == other.subscriber_count and \
                self.following == other.following and \
                self.user == other.user

        except AttributeError:
            return False

    def __str__(self):
        '''
        A string representation of this twitter.List instance.

        The return value is the same as the JSON string representation.

        Returns:
            A string representation of this twitter.List instance.
        '''
        return self.asJsonString()

    def asJsonString(self):
        '''A JSON string representation of this twitter.List instance.

        Returns:
            A JSON string representation of this twitter.List instance
        '''
        return simplejson.dumps(self.asDict(), sort_keys=True)

    def asDict(self):
        '''
        A dict representation of this twitter.List instance.

        The return value uses the same key names as the JSON representation.

        Return:
            A dict representing this twitter.List instance
        '''
        data = {}
        if self.id:
            data['id'] = self.id
        if self.name:
            data['name'] = self.name
        if self.slug:
            data['slug'] = self.slug
        if self.description:
            data['description'] = self.description
        if self.full_name:
            data['full_name'] = self.full_name
        if self.mode:
            data['mode'] = self.mode
        if self.uri:
            data['uri'] = self.uri
        if self.member_count is not None:
            data['member_count'] = self.member_count
        if self.subscriber_count is not None:
            data['subscriber_count'] = self.subscriber_count
        if self.following is not None:
            data['following'] = self.following
        if self.user is not None:
            data['user'] = self.user
        return data

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data:
            A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.List instance
        '''
        if 'user' in data:
            user = User.newFromJsonDict(data['user'])
        else:
            user = None
        return List(id=data.get('id', None),
            name=data.get('name', None),
            slug=data.get('slug', None),
            description=data.get('description', None),
            full_name=data.get('full_name', None),
            mode=data.get('mode', None),
            uri=data.get('uri', None),
            member_count=data.get('member_count', None),
            subscriber_count=data.get('subscriber_count', None),
            following=data.get('following', None),
            user=user)

class DirectMessage(object):
    '''
    A class representing the DirectMessage structure used by the twitter API.

    The DirectMessage structure exposes the following properties:

        direct_message.id
        direct_message.created_at
        direct_message.created_at_in_seconds # read only
        direct_message.sender_id
        direct_message.sender_screen_name
        direct_message.recipient_id
        direct_message.recipient_screen_name
        direct_message.text
    '''

    def __init__(self,
        id=None,
        created_at=None,
        sender_id=None,
        sender_screen_name=None,
        recipient_id=None,
        recipient_screen_name=None,
        text=None):
        '''
        An object to hold a Twitter direct message.

        This class is normally instantiated by the twitter.Api class and
        returned in a sequence.

        Note: Dates are posted in the form "Sat Jan 27 04:17:38 +0000 2007"

        Args:
            id:
                The unique id of this direct message. [Optional]
            created_at:
                The time this direct message was posted. [Optional]
            sender_id:
                The id of the twitter user that sent this message. [Optional]
            sender_screen_name:
                The name of the twitter user that sent this message. [Optional]
            recipient_id:
                The id of the twitter that received this message. [Optional]
            recipient_screen_name:
                The name of the twitter that received this message. [Optional]
            text:
                The text of this direct message. [Optional]
        '''
        self.id = id
        self.created_at = created_at
        self.sender_id = sender_id
        self.sender_screen_name = sender_screen_name
        self.recipient_id = recipient_id
        self.recipient_screen_name = recipient_screen_name
        self.text = text

    def getId(self):
        '''
        Get the unique id of this direct message.

        Returns:
            The unique id of this direct message
        '''
        return self._id

    def setId(self, id):
        '''
        Set the unique id of this direct message.

        Args:
            id:
                The unique id of this direct message
        '''
        self._id = id

    id = property(getId, setId, doc='The unique id of this direct message.')

    def getCreatedAt(self):
        '''
        Get the time this direct message was posted.

        Returns:
            The time this direct message was posted
        '''
        return self._created_at

    def setCreatedAt(self, created_at):
        '''
        Set the time this direct message was posted.

        Args:
            created_at:
                The time this direct message was created
        '''
        self._created_at = created_at

    created_at = property(getCreatedAt, setCreatedAt,
        doc='The time this direct message was posted.')

    def getCreatedAtInSeconds(self):
        '''
        Get the time this direct message was posted, in seconds since the epoch.

        Returns:
            The time this direct message was posted, in seconds since the epoch.
        '''
        return calendar.timegm(rfc822.parsedate(self.created_at))

    created_at_in_seconds = property(getCreatedAtInSeconds,
        doc="The time this direct message was posted, in seconds since the epoch")

    def getSenderId(self):
        '''
        Get the unique sender id of this direct message.

        Returns:
            The unique sender id of this direct message
        '''
        return self._sender_id

    def setSenderId(self, sender_id):
        '''
        Set the unique sender id of this direct message.

        Args:
            sender_id:
                The unique sender id of this direct message
        '''
        self._sender_id = sender_id

    sender_id = property(getSenderId, setSenderId,
        doc='The unique sender id of this direct message.')

    def getSenderScreenName(self):
        '''
        Get the unique sender screen name of this direct message.

        Returns:
            The unique sender screen name of this direct message
            '''
        return self._sender_screen_name

    def setSenderScreenName(self, sender_screen_name):
        '''
        Set the unique sender screen name of this direct message.

        Args:
            sender_screen_name:
                The unique sender screen name of this direct message
        '''
        self._sender_screen_name = sender_screen_name

    sender_screen_name = property(getSenderScreenName, setSenderScreenName,
        doc='The unique sender screen name of this direct message.')

    def getRecipientId(self):
        '''
        Get the unique recipient id of this direct message.

        Returns:
            The unique recipient id of this direct message
            '''
        return self._recipient_id

    def setRecipientId(self, recipient_id):
        '''
        Set the unique recipient id of this direct message.

        Args:
            recipient_id:
                The unique recipient id of this direct message
        '''
        self._recipient_id = recipient_id

    recipient_id = property(getRecipientId, setRecipientId,
        doc='The unique recipient id of this direct message.')

    def getRecipientScreenName(self):
        '''
        Get the unique recipient screen name of this direct message.

        Returns:
            The unique recipient screen name of this direct message
            '''
        return self._recipient_screen_name

    def setRecipientScreenName(self, recipient_screen_name):
        '''
        Set the unique recipient screen name of this direct message.

        Args:
            recipient_screen_name:
                The unique recipient screen name of this direct message
        '''
        self._recipient_screen_name = recipient_screen_name

    recipient_screen_name = property(getRecipientScreenName, setRecipientScreenName,
        doc='The unique recipient screen name of this direct message.')

    def getText(self):
        '''
        Get the text of this direct message.

        Returns:
            The text of this direct message.
            '''
        return self._text

    def setText(self, text):
        '''
        Set the text of this direct message.

        Args:
            text:
                The text of this direct message
        '''
        self._text = text

    text = property(getText, setText, doc='The text of this direct message')

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        try:
            return other and \
                self.id == other.id and \
                self.created_at == other.created_at and \
                self.sender_id == other.sender_id and \
                self.sender_screen_name == other.sender_screen_name and \
                self.recipient_id == other.recipient_id and \
                self.recipient_screen_name == other.recipient_screen_name and \
                self.text == other.text
        except AttributeError:
            return False

    def __str__(self):
        '''
        A string representation of this twitter.DirectMessage instance.

        The return value is the same as the JSON string representation.

        Returns:
            A string representation of this twitter.DirectMessage instance.
        '''
        return self.asJsonString()

    def asJsonString(self):
        '''
        A JSON string representation of this twitter.DirectMessage instance.

        Returns:
            A JSON string representation of this twitter.DirectMessage instance
        '''
        return simplejson.dumps(self.asDict(), sort_keys=True)

    def asDict(self):
        '''
        A dict representation of this twitter.DirectMessage instance.

        The return value uses the same key names as the JSON representation.

        Return:
            A dict representing this twitter.DirectMessage instance
        '''
        data = {}
        if self.id:
            data['id'] = self.id
        if self.created_at:
            data['created_at'] = self.created_at
        if self.sender_id:
            data['sender_id'] = self.sender_id
        if self.sender_screen_name:
            data['sender_screen_name'] = self.sender_screen_name
        if self.recipient_id:
            data['recipient_id'] = self.recipient_id
        if self.recipient_screen_name:
            data['recipient_screen_name'] = self.recipient_screen_name
        if self.text:
            data['text'] = self.text
        return data

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data:
                A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.DirectMessage instance
        '''
        return DirectMessage(created_at=data.get('created_at', None),
            recipient_id=data.get('recipient_id', None),
            sender_id=data.get('sender_id', None),
            text=data.get('text', None),
            sender_screen_name=data.get('sender_screen_name', None),
            id=data.get('id', None),
            recipient_screen_name=data.get('recipient_screen_name', None))


class Hashtag(object):
    ''' A class represeinting a twitter hashtag'''

    def __init__(self, text=None):
        self.text = text

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data:
                A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.Hashtag instance
        '''
        return Hashtag(text = data.get('text', None))


class Trend(object):
    ''' A class representing a trending topic'''

    def __init__(self, name=None, query=None, timestamp=None):
        self.name = name
        self.query = query
        self.timestamp = timestamp

    def __str__(self):
        return 'Name: %s\nQuery: %s\nTimestamp: %s\n' % (self.name, self.query, self.timestamp)

    @staticmethod
    def newFromJsonDict(data, timestamp = None):
        '''
        Create a new instance based on a JSON dict

        Args:
            data:
                A JSON dict
            timestamp:
                Gets set as the timestamp property of the new object

        Returns:
            A twitter.Trend object
        '''
        return Trend(name=data.get('name', None),
            query=data.get('query', None),
            timestamp=timestamp)


class Url(object):
    '''A class representing an URL contained in a tweet'''

    def __init__(self, url=None, expanded_url=None):
        self.url = url
        self.expanded_url = expanded_url

    @staticmethod
    def newFromJsonDict(data):
        '''
        Create a new instance based on a JSON dict.

        Args:
            data:
                A JSON dict, as converted from the JSON in the twitter API

        Returns:
            A twitter.Url instance
        '''
        return Url(url=data.get('url', None),
            expanded_url=data.get('expanded_url', None))


class Api(object):
    '''
    A python interface into the Twitter API

    By default, the Api caches results for 1 minute.

    Example usage:

        To create an instance of the twitter.Api class, with no authentication:

            >>> import twitter
            >>> api = twitter.Api()

        To fetch the most recently posted public twitter status messages:

            >>> statuses = api.getPublicTimeline()
            >>> print [s.user.name for s in statuses]
            [u'DeWitt', u'Kesuke Miyagi', u'ev', u'Buzz Andersen', u'Biz Stone'] #...

        To fetch a single user's public status messages, where "user" is either
        a Twitter "short name" or their user id.

            >>> statuses = api.getUserTimeline(user)
            >>> print [s.text for s in statuses]

        To use authentication, instantiate the twitter.Api class with a
        consumer key and secret; and the oAuth key and secret:

            >>> api = twitter.Api(consumer_key='twitter consumer key',
                    consumer_secret='twitter consumer secret',
                    access_token_key='the_key_given',
                    access_token_secret='the_key_secret')

        To fetch your friends (after being authenticated):

            >>> users = api.getFriends()
            >>> print [u.name for u in users]

        To post a twitter status message (after being authenticated):

            >>> status = api.postUpdate('I love python-twitter!')
            >>> print status.text
            I love python-twitter!

        There are many other methods, including:

            >>> api.postUpdates(status)
            >>> api.postDirectMessage(user, text)
            >>> api.getUser(user)
            >>> api.getReplies()
            >>> api.getUserTimeline(user)
            >>> api.getStatus(id)
            >>> api.destroyStatus(id)
            >>> api.getFriendsTimeline(user)
            >>> api.getFriends(user)
            >>> api.getFollowers()
            >>> api.getFeatured()
            >>> api.getDirectMessages()
            >>> api.postDirectMessage(user, text)
            >>> api.destroyDirectMessage(id)
            >>> api.destroyFriendship(user)
            >>> api.createFriendship(user)
            >>> api.getUserByEmail(email)
            >>> api.verifyCredentials()
    '''

    DEFAULT_CACHE_TIMEOUT = 60 * 60 * 24 * 90  # Cache for {{duration}} seconds.
    _API_REALM = 'Twitter API'

    def __init__(self,
        consumer_key=None,
        consumer_secret=None,
        access_token_key=None,
        access_token_secret=None,
        screen_name='',
        input_encoding=None,
        request_headers=None,
        cache=DEFAULT_CACHE,
        shortner=None,
        base_url=None,
        use_gzip_compression=False,
        debugHTTP=False):
        '''
        Instantiate a new twitter.Api object.

        Args:
            consumer_key:
                Your Twitter user's consumer_key.
            consumer_secret:
                Your Twitter user's consumer_secret.
            access_token_key:
                The oAuth access token key value you retrieved
                from running get_access_token.py.
            access_token_secret:
                The oAuth access token's secret, also retrieved
                from the get_access_token.py run.
            input_encoding:
                The encoding used to encode input strings. [Optional]
            request_header:
                A dictionary of additional HTTP request headers. [Optional]
            cache:
                The cache instance to use. Defaults to DEFAULT_CACHE.
                Use None to disable caching. [Optional]
            shortner:
                The shortner instance to use.  Defaults to None.
                See shorten_url.py for an example shortner. [Optional]
            base_url:
                The base URL to use to contact the Twitter API.
                Defaults to https://twitter.com. [Optional]
            use_gzip_compression:
                Set to True to tell enable gzip compression for any call
                made to Twitter.  Defaults to False. [Optional]
            debugHTTP:
                Set to True to enable debug output from urllib2 when performing
                any HTTP requests.  Defaults to False. [Optional]
        '''
        self.screen_name     = screen_name
        self.setCache(cache)
        self._urllib         = urllib2
        self._cache_timeout  = Api.DEFAULT_CACHE_TIMEOUT
        self._input_encoding = input_encoding
        self._use_gzip       = use_gzip_compression
        self._debugHTTP      = debugHTTP
        self._oauth_consumer = None

        self._initializeRequestHeaders(request_headers)
        self._initializeUserAgent()
        self._initializeDefaultParameters()

        if base_url is None:
            self.base_url = 'https://api.twitter.com/1'
        else:
            self.base_url = base_url

        if consumer_key is not None and (access_token_key is None or
            access_token_secret is None):
            print >> sys.stderr, 'Twitter now requires an oAuth Access Token for API calls.'
            print >> sys.stderr, 'If your using this library from a command line utility, please'
            print >> sys.stderr, 'run the the included get_access_token.py tool to generate one.'
            raise TwitterError('Twitter requires oAuth Access Token for all API access')

        self.setCredentials(consumer_key, consumer_secret, access_token_key, access_token_secret)
        self.next_cursor = -1
        self.previous_cursor = 0

    def setCredentials(self, consumer_key, consumer_secret, access_token_key=None, access_token_secret=None):
        '''
        Set the consumer_key and consumer_secret for this instance

        Args:
            consumer_key:
                The consumer_key of the twitter account.
            consumer_secret:
                The consumer_secret for the twitter account.
            access_token_key:
                The oAuth access token key value you retrieved
                from running get_access_token.py.
            access_token_secret:
                The oAuth access token's secret, also retrieved
                from the get_access_token.py run.
        '''
        self._consumer_key        = consumer_key
        self._consumer_secret     = consumer_secret
        self._access_token_key    = access_token_key
        self._access_token_secret = access_token_secret
        self._oauth_consumer      = None

        if consumer_key is not None and consumer_secret is not None and \
            access_token_key is not None and access_token_secret is not None:
            self._signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
            self._signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
            self._oauth_token    = oauth.Token(key=access_token_key, secret=access_token_secret)
            self._oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

    def clearCredentials(self):
        '''Clear the any credentials for this instance'''
        self._consumer_key        = None
        self._consumer_secret     = None
        self._access_token_key    = None
        self._access_token_secret = None
        self._oauth_consumer      = None

    def getPublicTimeline(self, since_id=None, include_rts=None, include_entities=None, **kw):
        '''
        Fetch the sequence of public twitter.Status message for all users.

        Args:
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            include_rts:
                If True, the timeline will contain native retweets (if they
                exist) in addition to the standard stream of tweets. [Optional]
            include_entities:
                If True, each tweet will include a node called "entities,".
                This node offers a variety of metadata about the tweet in a
                discreet structure, including: user_mentions, urls, and
                hashtags. [Optional]

        Returns:
            An sequence of twitter.Status instances, one for each message
        '''
        parameters = {}
        if since_id:
            parameters['since_id'] = since_id
        if include_rts:
            parameters['include_rts'] = 1
        if include_entities:
            parameters['include_entities'] = 1
        url  = '%s/statuses/public_timeline.json' % self.base_url
        json = self._fetchUrl(url,  parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def filterPublicTimeline(self, term, since_id=None, **kw):
        '''
        Filter the public twitter timeline by a given search term on
        the local machine.

        Args:
            term:
                term to search by.
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]

        Returns:
            A sequence of twitter.Status instances, one for each message
            containing the term
        '''
        statuses = self.getPublicTimeline(since_id)
        results  = []
        for s in statuses:
            if s.text.lower().find(term.lower()) != -1:
                results.append(s)
        return results

    def getSearch(self,
        term=None,
        geocode=None,
        since_id=None,
        per_page=15,
        page=1,
        lang="en",
        show_user="true",
        query_users=False,
        **kw):
        '''
        Return twitter search results for a given term.

        Args:
            term:
                term to search by. Optional if you include geocode.
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            geocode:
                geolocation information in the form (latitude, longitude, radius)
                [Optional]
            per_page:
                number of results to return.  Default is 15 [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]
            lang:
                language for results.  Default is English [Optional]
            show_user:
                prefixes screen name in status
            query_users:
                If set to False, then all users only have screen_name and
                profile_image_url available.
                If set to True, all information of users are available,
                but it uses lots of request quota, one per status.

        Returns:
            A sequence of twitter.Status instances, one for each message containing
            the term
        '''
        # Build request parameters.
        parameters = {}
        if since_id:
            parameters['since_id'] = since_id
        if term is None and geocode is None:
            return []
        if term is not None:
            parameters['q'] = term
        if geocode is not None:
            parameters['geocode'] = ','.join(map(str, geocode))
        parameters['show_user'] = show_user
        parameters['lang'] = lang
        parameters['rpp'] = per_page
        parameters['page'] = page
        # Make and send requests.
        url  = 'http://search.twitter.com/search.json'
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        results = []
        for x in data['results']:
            temp = Status.newFromJsonDict(x)
            if query_users:
                # Build user object with new request.
                temp.user = self.getUser(urllib.quote(x['from_user']))
            else:
                temp.user = User(screen_name=x['from_user'], profile_image_url=x['profile_image_url'])
            results.append(temp)
        # Return built list of statuses.
        return results # [Status.newFromJsonDict(x) for x in data['results']]

    def getTrendsCurrent(self, exclude=None, **kw):
        '''
        Get the current top trending topics

        Args:
            exclude:
                Appends the exclude parameter as a request parameter.
                Currently only exclude=hashtags is supported. [Optional]

        Returns:
            A list with 10 entries. Each entry contains the twitter.
        '''
        parameters = {}
        if exclude:
            parameters['exclude'] = exclude
        url = '%s/trends/current.json' % self.base_url
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        trends = []
        for t in data['trends']:
            for item in data['trends'][t]:
                trends.append(Trend.newFromJsonDict(item, timestamp = t))
        return trends

    def getTrendsDaily(self, exclude=None, startdate=None, **kw):
        '''
        Get the current top trending topics for each hour in a given day

        Args:
            startdate:
                The start date for the report.
                Should be in the format YYYY-MM-DD. [Optional]
            exclude:
                Appends the exclude parameter as a request parameter.
                Currently only exclude=hashtags is supported. [Optional]

        Returns:
            A list with 24 entries. Each entry contains the twitter.
            Trend elements that were trending at the corresponding hour of the day.
        '''
        parameters = {}
        if exclude:
            parameters['exclude'] = exclude
        if not startdate:
            startdate = time.strftime('%Y-%m-%d', time.gmtime())
        parameters['date'] = startdate
        url = '%s/trends/daily.json' % self.base_url
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        trends = []
        for i in xrange(24):
            trends.append(None)
        for t in data['trends']:
            idx = int(time.strftime('%H', time.strptime(t, '%Y-%m-%d %H:%M')))
            trends[idx] = [Trend.newFromJsonDict(x, timestamp = t)
                for x in data['trends'][t]]
        return trends

    def getTrendsWeekly(self, exclude=None, startdate=None, **kw):
        '''
        Get the top 30 trending topics for each day in a given week.

        Args:
            startdate:
                The start date for the report.
                Should be in the format YYYY-MM-DD. [Optional]
            exclude:
                Appends the exclude parameter as a request parameter.
                Currently only exclude=hashtags is supported. [Optional]

        Returns:
            A list with each entry contains the twitter.
            Trend elements of trending topics for the corrsponding day of the week
        '''
        parameters = {}
        if exclude:
            parameters['exclude'] = exclude
        if not startdate:
            startdate = time.strftime('%Y-%m-%d', time.gmtime())
        parameters['date'] = startdate
        url = '%s/trends/weekly.json' % self.base_url
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        trends = []
        for i in xrange(7):
            trends.append(None)
        # Use the epochs of the dates as keys for a dictionary.
        times = dict([(calendar.timegm(time.strptime(t, '%Y-%m-%d')), t)
            for t in data['trends']])
        cnt = 0
        # Create the resulting structure ordered by the epochs of the dates.
        for e in sorted(times.keys()):
            trends[cnt] = [Trend.newFromJsonDict(x, timestamp = times[e])
                for x in data['trends'][times[e]]]
            cnt +=1
        return trends

    def getFriendsTimeline(self,
        user=None,
        count=None,
        page=None,
        since_id=None,
        retweets=None,
        include_entities=None,
        **kw):
        '''
        Fetch the sequence of twitter.Status messages for a user's friends

        The twitter.Api instance must be authenticated if the user is private.

        Args:
            user:
                Specifies the ID or screen name of the user for whom to return
                the friends_timeline.  If not specified then the authenticated
                user set in the twitter.Api instance will be used.  [Optional]
            count:
                Specifies the number of statuses to retrieve. May not be
                greater than 100. [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            retweets:
                If True, the timeline will contain native retweets. [Optional]
            include_entities:
                If True, each tweet will include a node called "entities,".
                This node offers a variety of metadata about the tweet in a
                discreet structure, including: user_mentions, urls, and
                hashtags. [Optional]

        Returns:
            A sequence of twitter.Status instances, one for each message
        '''
        if not user and not self._oauth_consumer:
            raise TwitterError("User must be specified if API is not authenticated.")
        url = '%s/statuses/friends_timeline' % self.base_url
        if user:
            url = '%s/%s.json' % (url, user)
        else:
            url = '%s.json' % url
            kw['account_specific'] = True
        parameters = {}
        if count is not None:
            try:
                if int(count) > 100:
                    raise TwitterError("'count' may not be greater than 100")
            except ValueError:
                raise TwitterError("'count' must be an integer")
            parameters['count'] = count
        if page is not None:
            try:
                parameters['page'] = int(page)
            except ValueError:
                raise TwitterError("'page' must be an integer")
        if max_id:
            try:
                parameters['max_id'] = int(max_id)
            except ValueError:
                raise TwitterError("'max_id' must be an integer")
        if since_id:
            parameters['since_id'] = since_id
        if retweets:
            parameters['include_rts'] = True
        if include_entities:
            parameters['include_entities'] = True
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def getUserTimeline(self,
        id=None,
        user_id=None,
        screen_name=None,
        since_id=None,
        max_id=None,
        count=None,
        page=None,
        include_rts=None,
        include_entities=None,
        **kw):
        '''
        Fetch the sequence of public Status messages for a single user.

        The twitter.Api instance must be authenticated if the user is private.

        Args:
            id:
                Specifies the ID or screen name of the user for whom to return
                the user_timeline. [Optional]
            user_id:
                Specfies the ID of the user for whom to return the
                user_timeline. Helpful for disambiguating when a valid user ID
                is also a valid screen name. [Optional]
            screen_name:
                Specfies the screen name of the user for whom to return the
                user_timeline. Helpful for disambiguating when a valid screen
                name is also a user ID. [Optional]
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            max_id:
                Returns only statuses with an ID less than (that is, older
                than) or equal to the specified ID. [Optional]
            count:
                Specifies the number of statuses to retrieve. May not be
                greater than 200.    [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]
            include_rts:
                If True, the timeline will contain native retweets (if they
                exist) in addition to the standard stream of tweets. [Optional]
            include_entities:
                If True, each tweet will include a node called "entities,".
                This node offers a variety of metadata about the tweet in a
                discreet structure, including: user_mentions, urls, and
                hashtags. [Optional]

        Returns:
            A sequence of Status instances, one for each message up to count
        '''
        parameters = {}
        if id:
            url = '%s/statuses/user_timeline/%s.json' % (self.base_url, id)
        elif user_id:
            url = '%s/statuses/user_timeline.json?user_id=%d' % (self.base_url, user_id)
        elif screen_name:
            url = ('%s/statuses/user_timeline.json?screen_name=%s' % (self.base_url,
                         screen_name))
        elif not self._oauth_consumer:
            raise TwitterError("User must be specified if API is not authenticated.")
        else:
            url = '%s/statuses/user_timeline.json' % self.base_url
            kw['account_specific'] = True

        if since_id:
            try:
                parameters['since_id'] = long(since_id)
            except:
                raise TwitterError("since_id must be an integer")

        if max_id:
            try:
                parameters['max_id'] = long(max_id)
            except:
                raise TwitterError("max_id must be an integer")

        if count:
            try:
                parameters['count'] = int(count)
            except:
                raise TwitterError("count must be an integer")

        if page:
            try:
                parameters['page'] = int(page)
            except:
                raise TwitterError("page must be an integer")

        if include_rts:
            parameters['include_rts'] = 1

        if include_entities:
            parameters['include_entities'] = 1

        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def getStatus(self, id, **kw):
        '''
        Returns a single status message.

        The twitter.Api instance must be authenticated if the
        status message is private.

        Args:
            id:
                The numeric ID of the status you are trying to retrieve.

        Returns:
            A twitter.Status instance representing that status message
        '''
        try:
            if id:
                long(id)
        except:
            raise TwitterError("id must be an long integer")
        url = '%s/statuses/show/%s.json' % (self.base_url, id)
        json = self._fetchUrl(url, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def getHomeTimeline(self, since_id=None, max_id=None, count=None, page=None):
        '''
        Fetch your home timeline

        The twitter.Api instance must be authenticated.

        Args:
            since_id:
                Returns only public statuses with an ID greater than (that is,
                more recent than) the specified ID. [optional]
            max_id:
                Returns only statuses with an ID less than (that is, older
                than) or equal to the specified ID. [optional]
            count:
                Specifies the number of statuses to retrieve. May not be
                greater than 200.  [optional]
            page:
                 Specifies the page of results to retrieve. Note: there are
                 pagination limits. [optional]

        Returns:
            A sequence of Status instances, one for each message up to count
        '''
        parameters = {}
        if not self._oauth_consumer:
            raise TwitterError("User must be authenticated.")
        else:
            url = '%s/statuses/home_timeline.json' % self.base_url
        if since_id:
            try:
                parameters['since_id'] = long(since_id)
            except:
                raise TwitterError("since_id must be an integer")
        if max_id:
            try:
                parameters['max_id'] = long(max_id)
            except:
                raise TwitterError("max_id must be an integer")
        if count:
            try:
                parameters['count'] = int(count)
            except:
                raise TwitterError("count must be an integer")
        if page:
            try:
                parameters['page'] = int(page)
            except:
                raise TwitterError("page must be an integer")
        json = self._FetchUrl(url, parameters=parameters)
        data = simplejson.loads(json)
        self._CheckForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def destroyStatus(self, id, **kw):
        '''
        Destroys the status specified by the required ID parameter.

        The twitter.Api instance must be authenticated and the
        authenticating user must be the author of the specified status.

        Args:
            id:
                The numerical ID of the status you're trying to destroy.

        Returns:
            A twitter.Status instance representing the destroyed status message
        '''
        try:
            if id:
                long(id)
        except:
            raise TwitterError("id must be an integer")
        url = '%s/statuses/destroy/%s.json' % (self.base_url, id)
        json = self._fetchUrl(url, post_data={'id': id}, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def postUpdate(self, status, in_reply_to_status_id=None, **kw):
        '''
        Post a twitter status message from the authenticated user.

        The twitter.Api instance must be authenticated.

        Args:
            status:
                The message text to be posted.
                Must be less than or equal to 140 characters.
            in_reply_to_status_id:
                The ID of an existing status that the status to be posted is
                in reply to.  This implicitly sets the in_reply_to_user_id
                attribute of the resulting status to the user ID of the
                message being replied to.  Invalid/missing status IDs will be
                ignored. [Optional]

        Returns:
            A twitter.Status instance representing the message posted.
        '''
        if not self._oauth_consumer:
            raise TwitterError('The twitter.Api instance must be authenticated.')
        url = '%s/statuses/update.json' % self.base_url
        if isinstance(status, unicode) or self._input_encoding is None:
            u_status = status
        else:
            u_status = unicode(status, self._input_encoding)
        if len(u_status) > CHARACTER_LIMIT:
            raise TwitterError('Text must be less than or equal to %d characters. '
                'Consider using the postUpdates() method instead' % CHARACTER_LIMIT)
        data = {'status': u_status.encode('utf-8')}
        if in_reply_to_status_id:
            data['in_reply_to_status_id'] = in_reply_to_status_id
        json = self._fetchUrl(url, post_data=data, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def RetweetPost(self, id):
        '''
        Retweet some twitter status.

        The twitter.Api instance must be authenticated.

        Args:
            id:
                The ID of an existing status that should be retweeted.
        Returns:
            A twitter.Status instance representing the message posted.
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        url = '%s/statuses/retweet/%d.json' % (self.base_url, id)
        json = self._FetchUrl(url, post_data={'':None})
        data = simplejson.loads(json)
        self._CheckForTwitterError(data)
        return Status.newFromJsonDict(data)

    def postUpdates(self, status, continuation=None, **kw):
        '''
        Post one or more twitter status messages from the authenticated user.

        Unlike api.postUpdate, this method will post multiple status updates
        if the message is longer than 140 characters.

        The twitter.Api instance must be authenticated.

        Args:
            status:
                The message text to be posted.
                May be longer than 140 characters.
            continuation:
                The character string, if any, to be appended to all but the
                last message.  Note that Twitter strips trailing '...' strings
                from messages.  Consider using the unicode \u2026 character
                (horizontal ellipsis) instead. [Defaults to None]
            **kw:
                See api.postUpdate for a list of accepted parameters.

        Returns:
            A of list twitter.Status instance representing the messages posted.
        '''
        results = list()
        if continuation is None:
            continuation = ''
        line_length = CHARACTER_LIMIT - len(continuation)
        lines = textwrap.wrap(status, line_length)
        for line in lines[0:-1]:
            results.append(self.postUpdate(line + continuation, **kw))
        results.append(self.postUpdate(lines[-1], **kw))
        return results

    def retweet(self, status_id, **kw):
        '''
        Post a twitter status message from the authenticated user.

        The twitter.Api instance must be authenticated.

        Args:
            status_id:
                The numerical ID of the tweet your are retweeting.

        Returns:
            A twitter.Status instance representing the message posted.
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        url = '%s/statuses/retweet/%s.json' % (self.base_url, status_id)
        data = {'id': status_id}
        json = self._fetchUrl(url, post_data=data, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def getUserRetweets(self, count=None, since_id=None, max_id=None, include_entities=False, **kw):
        '''
        Fetch the sequence of retweets made by a single user.

        The twitter.Api instance must be authenticated.

        Args:
            count:
                The number of status messages to retrieve. [Optional]
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            max_id:
                Returns results with an ID less than (that is, older than) or
                equal to the specified ID. [Optional]
            include_entities:
                If True, each tweet will include a node called "entities,".
                This node offers a variety of metadata about the tweet in a
                discreet structure, including: user_mentions, urls, and
                hashtags. [Optional]

        Returns:
            A sequence of twitter.Status instances, one for each message up to count
        '''
        url = '%s/statuses/retweeted_by_me.json' % self.base_url
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        parameters = {}
        if count is not None:
            try:
                if int(count) > 100:
                    raise TwitterError("'count' may not be greater than 100")
            except ValueError:
                raise TwitterError("'count' must be an integer")
        if count:
            parameters['count'] = count
        if since_id:
            parameters['since_id'] = since_id
        if include_entities:
            parameters['include_entities'] = True
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def getReplies(self, since=None, since_id=None, page=None, **kw):
        '''
        Get a sequence of status messages representing the 20 most
        recent replies (status updates prefixed with @twitterID) to the
        authenticating user.

        Args:
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]
            since:

        Returns:
            A sequence of twitter.Status instances, one for each reply to the user.
        '''
        url = '%s/statuses/replies.json' % self.base_url
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        parameters = {}
        if since:
            parameters['since'] = since
        if since_id:
            parameters['since_id'] = since_id
        if page:
            parameters['page'] = page
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def getRetweets(self, statusid, **kw):
        '''
        Returns up to 100 of the first retweets of the tweet identified
        by statusid

        Args:
            statusid:
                The ID of the tweet for which retweets should be searched for

        Returns:
            A list of twitter.Status instances, which are retweets of statusid
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instsance must be authenticated.")
        url = '%s/statuses/retweets/%s.json?include_entities=true&include_rts=true' % (self.base_url, statusid)
        parameters = {}
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(s) for s in data]

    def getFriends(self, user=None, cursor=-1, **kw):
        '''
        Fetch the sequence of twitter.User instances, one for each friend.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The twitter name or id of the user whose friends you are fetching.
                If not specified, defaults to the authenticated user. [Optional]

        Returns:
            A sequence of twitter.User instances, one for each friend
        '''
        if not user and not self._oauth_consumer:
            raise TwitterError("twitter.Api instance must be authenticated")
        if user:
            url = '%s/statuses/friends/%s.json' % (self.base_url, user)
        else:
            url = '%s/statuses/friends.json' % self.base_url
            kw['account_specific'] = True
        parameters = {}
        parameters['cursor'] = cursor
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [User.newFromJsonDict(x) for x in data['users']]

    def getFriendIDs(self, user=None, cursor=-1, **kw):
        '''
        Returns a list of twitter user id's for every person
        the specified user is following.

        Args:
            user:
                The id or screen_name of the user to retrieve the id list for
                [Optional]

        Returns:
            A list of integers, one for each user id.
        '''
        if not user and not self._oauth_consumer:
            raise TwitterError("twitter.Api instance must be authenticated")
        if user:
            url = '%s/friends/ids/%s.json' % (self.base_url, user)
        else:
            url = '%s/friends/ids.json' % self.base_url
            kw['account_specific'] = True
        parameters = {}
        parameters['cursor'] = cursor
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return data

    def getFollowerIDs(self, cursor=-1, **kw):
        '''
        Fetch the sequence of twitter.User instances, one for each follower

        The twitter.Api instance must be authenticated.

        Returns:
            A sequence of twitter.User instances, one for each follower
        '''
        url = 'http://twitter.com/followers/ids.json'
        parameters = {}
        parameters['cursor'] = cursor
        if kw.get('user_id', False):
            parameters['user_id'] = kw.get('user_id')
        if kw.get('screen_name', False):
            parameters['screen_name'] = kw.get('screen_name')
        if not (kw.get('user_id', False) or kw.get('screen_name', False)):
            kw['account_specific'] = True
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return data

    def getFollowers(self, cursor=-1, **kw):
        '''
        Fetch the sequence of twitter.User instances, one for each follower

        The twitter.Api instance must be authenticated.

        Args:
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]
            cursor:
                "page" value that Twitter will use to start building the
                list sequence from.  -1 to start at the beginning.
                Twitter will return in the result the values for next_cursor
                and previous_cursor. [Optional]

        Returns:
            A sequence of twitter.User instances, one for each follower
        '''
        if not self._oauth_consumer:
            raise TwitterError("twitter.Api instance must be authenticated")
        url = '%s/statuses/followers.json' % self.base_url
        parameters = {}
        parameters['cursor'] = cursor
        if kw.get('user_id', False):
            parameters['user_id'] = kw.get('user_id')
        if kw.get('screen_name', False):
            parameters['screen_name'] = kw.get('screen_name')
        if not (kw.get('user_id', False) or kw.get('screen_name', False)):
            kw['account_specific'] = True
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [User.newFromJsonDict(x) for x in data['users']]

    def getFeatured(self, **kw):
        '''
        Fetch the sequence of twitter.User instances featured on twitter.com

        The twitter.Api instance must be authenticated.

        Returns:
            A sequence of twitter.User instances
        '''
        url = '%s/statuses/featured.json' % self.base_url
        json = self._fetchUrl(url, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [User.newFromJsonDict(x) for x in data]

    def usersLookup(self, user_id=None, screen_name=None, users=None, **kw):
        '''
        Fetch extended information for the specified users.

        Users may be specified either as lists of either user_ids,
        screen_names, or twitter.User objects. The list of users that
       are queried is the union of all specified parameters.

        The twitter.Api instance must be authenticated.

        Args:
            user_id:
                A list of user_ids to retrieve extended information.
                [Optional]
            screen_name:
                A list of screen_names to retrieve extended information.
                [Optional]
            users:
                A list of twitter.User objects to retrieve extended information.
                [Optional]

        Returns:
            A list of twitter.User objects for the requested users
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        if not user_id and not screen_name and not users:
            raise TwitterError("Specify at least on of user_id, screen_name, or users.")
        url = '%s/users/lookup.json' % self.base_url
        parameters = {}
        uids = list()
        if user_id:
            uids.extend(user_id)
        if users:
            uids.extend([u.id for u in users])
        if len(uids):
            parameters['user_id'] = ','.join(["%s" % u for u in uids])
        if screen_name:
            parameters['screen_name'] = ','.join(screen_name)
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [User.newFromJsonDict(u) for u in data]

    def getUser(self, user=None, **kw):
        '''
        Returns a single user.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The twitter name or id of the user to retrieve.  If None, then the
                current authenticated user will be returned.

        Returns:
            A twitter.User instance representing that user
        '''
        if user is None:
            user = self.screen_name
            kw['account_specific'] = True
        url = '%s/users/show/%s.json' % (self.base_url, user.strip())
        json = self._fetchUrl(url, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def getDirectMessages(self, since=None, since_id=None, page=None, **kw):
        '''
        Returns a list of the direct messages sent to the authenticating user.

        The twitter.Api instance must be authenticated.

        Args:
            since:
                Narrows the returned results to just those statuses created
                after the specified HTTP-formatted date. [Optional]
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]

        Returns:
            A sequence of twitter.DirectMessage instances
        '''
        url = '%s/direct_messages.json' % self.base_url
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        parameters = {}
        if since:
            parameters['since'] = since
        if since_id:
            parameters['since_id'] = since_id
        if page:
            parameters['page'] = page
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [DirectMessage.newFromJsonDict(x) for x in data]

    def postDirectMessage(self, user, text):
        '''
        Post a twitter direct message from the authenticated user

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The ID or screen name of the recipient user.
            text:
                The message text to be posted.  Must be less than 140 characters.

        Returns:
            A twitter.DirectMessage instance representing the message posted
        '''
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        url = '%s/direct_messages/new.json' % self.base_url
        data = {'text': text, 'user': user}
        json = self._fetchUrl(url, post_data=data)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return DirectMessage.newFromJsonDict(data)

    def destroyDirectMessage(self, id):
        '''
        Destroys the direct message specified in the required ID parameter.

        The twitter.Api instance must be authenticated, and the
        authenticating user must be the recipient of the specified direct
        message.

        Args:
            id:
                The id of the direct message to be destroyed

        Returns:
            A twitter.DirectMessage instance representing the message destroyed
        '''
        url = '%s/direct_messages/destroy/%s.json' % (self.base_url, id)
        json = self._fetchUrl(url, post_data={'id': id})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return DirectMessage.newFromJsonDict(data)

    def createFriendship(self, user):
        '''
        Befriends the user specified in the user parameter as the authenticating user.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The ID or screen name of the user to befriend.

        Returns:
            A twitter.User instance representing the befriended user.
        '''
        url = '%s/friendships/create/%s.json' % (self.base_url, user)
        json = self._fetchUrl(url, post_data={'user': user})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def destroyFriendship(self, user):
        '''
        Discontinues friendship with the user specified in the user parameter.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The ID or screen name of the user  with whom to discontinue friendship.

        Returns:
            A twitter.User instance representing the discontinued friend.
        '''
        url = '%s/friendships/destroy/%s.json' % (self.base_url, user)
        json = self._fetchUrl(url, post_data={'user': user})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def createFavorite(self, status):
        '''
        Favorites the status specified in the status parameter as the authenticating user.
        Returns the favorite status when successful.

        The twitter.Api instance must be authenticated.

        Args:
            status:
                The twitter.Status instance to mark as a favorite.

        Returns:
            A twitter.Status instance representing the newly-marked favorite.
        '''
        url = '%s/favorites/create/%s.json' % (self.base_url, status.id)
        json = self._fetchUrl(url, post_data={'id': status.id})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def destroyFavorite(self, status):
        '''
        Un-favorites the status specified in the ID parameter as the authenticating user.
        Returns the un-favorited status in the requested format when successful.

        The twitter.Api instance must be authenticated.

        Args:
            status:
                The twitter.Status to unmark as a favorite.

        Returns:
            A twitter.Status instance representing the newly-unmarked favorite.
        '''
        url = '%s/favorites/destroy/%s.json' % (self.base_url, status.id)
        json = self._fetchUrl(url, post_data={'id': status.id})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return Status.newFromJsonDict(data)

    def getFavorites(self, user=None, page=None, **kw):
        '''
        Return a list of Status objects representing favorited tweets.
        By default, returns the (up to) 20 most recent tweets for the
        authenticated user.

        Args:
            user:
                The twitter name or id of the user whose favorites you are fetching.
                If not specified, defaults to the authenticated user. [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]

        Returns:
            A sequence of twitter.Favorite instances.
        '''
        parameters = {}
        if page:
            parameters['page'] = page
        if user:
            url = '%s/favorites/%s.json' % (self.base_url, user)
        elif not user and not self._oauth_consumer:
            raise TwitterError("User must be specified if API is not authenticated.")
        else:
            url = '%s/favorites.json' % self.base_url
            kw['account_specific'] = True
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def getMentions(self, since_id=None, max_id=None, page=None, **kw):
        '''
        Returns the 20 most recent mentions (status containing @twitterID)
        for the authenticating user.

        Args:
            since_id:
                Returns results with an ID greater than (that is, more recent
                than) the specified ID. There are limits to the number of
                Tweets which can be accessed through the API. If the limit of
                Tweets has occured since the since_id, the since_id will be
                forced to the oldest ID available. [Optional]
            max_id:
                Returns only statuses with an ID less than
                (that is, older than) the specified ID.  [Optional]
            page:
                Specifies the page of results to retrieve.
                Note: there are pagination limits. [Optional]

        Returns:
            A sequence of twitter.Status instances, one for each mention of the user.
        '''
        url = '%s/statuses/mentions.json' % self.base_url
        if not self._oauth_consumer:
            raise TwitterError("The twitter.Api instance must be authenticated.")
        parameters = {}
        if since_id:
            parameters['since_id'] = since_id
        if max_id:
            parameters['max_id'] = max_id
        if page:
            parameters['page'] = page
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [Status.newFromJsonDict(x) for x in data]

    def createList(self, user, name, mode=None, description=None):
        '''
        Creates a new list with the specified name.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                Twitter name or id to create the list for.
            name:
                New name for the list.
            mode:
                'public' or 'private'.
                Defaults to 'public'. [Optional]
            description:
                Description of the list. [Optional]

        Returns:
            A twitter.List instance representing the new list.
        '''
        # Make sure the list doesn't already exist.
        listOfLists = self.getLists(user, **{'cache_timeout': 0})
        lists = map(lambda l: l.name, listOfLists)
        if name in lists:
            return listOfLists[lists.index(name)]
        url = '%s/%s/lists.json' % (self.base_url, user)
        parameters = {'name': name}
        if mode is not None:
            parameters['mode'] = mode
        if description is not None:
            parameters['description'] = description
        json = self._fetchUrl(url, post_data=parameters)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return List.newFromJsonDict(data)

    def addUserToList(self, user, list_id):
        '''
        Adds a user to a list with the specified name.

        Args:
            user:
                Twitter screen name or id.
            list_id:
                List name.

        Returns:
            A twitter.List instance repesenting the updated list.
        '''
        url = '%s/%s/%s/members.json' % (self.base_url, self.screen_name, list_id)
        parameters = {'id': user}
        json = self._fetchUrl(url, post_data=parameters)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return List.newFromJsonDict(data)

    def destroyList(self, user, id):
        '''
        Destroys the list from the given user

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The user to remove the list from.
            id:
                The slug or id of the list to remove.

        Returns:
            A twitter.List instance representing the removed list.
        '''
        url = '%s/%s/lists/%s.json' % (self.base_url, user, id)
        json = self._fetchUrl(url, post_data={'_method': 'DELETE'})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return List.newFromJsonDict(data)

    def createSubscription(self, owner, list):
        '''
        Creates a subscription to a list by the authenticated user

        The twitter.Api instance must be authenticated.

        Args:
            owner:
                User name or id of the owner of the list being subscribed to.
            list:
                The slug or list id to subscribe the user to

        Returns:
            A twitter.List instance representing the list subscribed to
        '''
        url = '%s/%s/%s/subscribers.json' % (self.base_url, owner, list)
        json = self._fetchUrl(url, post_data={'list_id': list})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return List.newFromJsonDict(data)

    def destroySubscription(self, owner, list):
        '''
        Destroys the subscription to a list for the authenticated user

        The twitter.Api instance must be authenticated.

        Args:
            owner:
                The user id or screen name of the user that owns the
                list that is to be unsubscribed from
            list:
                The slug or list id of the list to unsubscribe from

        Returns:
            A twitter.List instance representing the removed list.
        '''
        url = '%s/%s/%s/subscribers.json' % (self.base_url, owner, list)
        json = self._fetchUrl(url, post_data={'_method': 'DELETE', 'list_id': list})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return List.newFromJsonDict(data)

    def getSubscriptions(self, user, cursor=-1, **kw):
        '''
        Fetch the sequence of Lists that the given user is subscribed to

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The twitter name or id of the user
            cursor:
                "page" value that Twitter will use to start building the
                list sequence from.  -1 to start at the beginning.
                Twitter will return in the result the values for next_cursor
                and previous_cursor. [Optional]

        Returns:
            A sequence of twitter.List instances, one for each list
        '''
        if not self._oauth_consumer:
            raise TwitterError("twitter.Api instance must be authenticated")
        url = '%s/%s/lists/subscriptions.json' % (self.base_url, user)
        parameters = {}
        parameters['cursor'] = cursor
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [List.newFromJsonDict(x) for x in data['lists']]

    def getLists(self, user, cursor=-1, **kw):
        '''
        Fetch the sequence of lists for a user.

        The twitter.Api instance must be authenticated.

        Args:
            user:
                The twitter name or id of the user whose friends you are fetching.
                If the passed in user is the same as the authenticated user
                then you will also receive private list data.
            cursor:
                "page" value that Twitter will use to start building the
                list sequence from.  -1 to start at the beginning.
                Twitter will return in the result the values for next_cursor
                and previous_cursor. [Optional]

        Returns:
            A sequence of twitter.List instances, one for each list
        '''
        if not self._oauth_consumer:
            raise TwitterError('twitter.Api instance must be authenticated')
        url = '%s/%s/lists.json' % (self.base_url, user)
        parameters = {}
        parameters['cursor'] = cursor
        json = self._fetchUrl(url, parameters=parameters, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return [List.newFromJsonDict(x) for x in data['lists']]

    def getUserByEmail(self, email, **kw):
        '''
        Returns a single user by email address.

        Args:
            email:
                The email of the user to retrieve.

        Returns:
            A twitter.User instance representing that user.
        '''
        url = '%s/users/show.json?email=%s' % (self.base_url, email)
        json = self._fetchUrl(url, **kw)
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def updateProfileImageUrl(self, image_url, **kw):
        '''
        @XXX @TODO THIS DOES NOT CURRENTLY WORK.  MULTI-MIME PART UPLOAD SUPPORT DOES NOT EXIST RIGHT NOW IN THIS LIB.
        Updates the profile image for the currently logged in user.

        Args:
            image_url:
                The address to retrieve the image from.
            **kw:
                'include_entities', which can be True or False.

        Returns:
            A twitter.User instance representing the user.
        '''
        raise Exception('FATAL: updateProfileImageUrl DOES NOT CURRENTLY WORK.' + \
            'MULTI-MIME PART UPLOAD SUPPORT DOES NOT EXIST RIGHT NOW IN THIS LIB.')
        url = '%s/account/update_profile_image.json' % self.base_url
        json = self._fetchUrl(url, **{'image_url': image_url})
        #    post_data={
        #        'image': wget(image_url),
        #        'include_entities': kw.get('include_entities', True)
        #    }
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def verifyCredentials(self):
        '''
        Returns a twitter.User instance if the authenticating user is valid.

        Returns:
            A twitter.User instance representing that user if the
            credentials are valid, None otherwise.
        '''
        if not self._oauth_consumer:
            raise TwitterError("Api instance must first be given user credentials.")
        url = '%s/account/verify_credentials.json' % self.base_url
        try:
            json = self._fetchUrl(url, **{'account_specific': True})
        except urllib2.HTTPError, http_error:
            if http_error.code == httplib.UNAUTHORIZED:
                return None
            else:
                raise http_error
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return User.newFromJsonDict(data)

    def setCache(self, cache):
        '''
        Override the default cache.  Set to None to prevent caching.

        Args:
            cache:
                An instance that supports the same API as the twitter._FileCache
        '''
        if cache == DEFAULT_CACHE:
            self._cache = _FileCache()
        else:
            self._cache = cache

    def setUrllib(self, urllib):
        '''
        Override the default urllib implementation.

        Args:
            urllib:
                An instance that supports the same API as the urllib2 module
        '''
        self._urllib = urllib

    def setCacheTimeout(self, cache_timeout):
        '''
        Override the default cache timeout.

        Args:
            cache_timeout:
                Time, in seconds, that responses should be reused.
        '''
        self._cache_timeout = cache_timeout

    def setUserAgent(self, user_agent):
        '''
        Override the default user agent

        Args:
            user_agent:
                A string that should be send to the server as the User-agent
        '''
        self._request_headers['User-Agent'] = user_agent

    def setXTwitterHeaders(self, client, url, version):
        '''
        Set the X-Twitter HTTP headers that will be sent to the server.

        Args:
            client:
                The client name as a string.  Will be sent to the server as
                the 'X-Twitter-Client' header.
            url:
                The URL of the meta.xml as a string.  Will be sent to the server
                as the 'X-Twitter-Client-URL' header.
            version:
                The client version as a string.  Will be sent to the server
                as the 'X-Twitter-Client-Version' header.
        '''
        self._request_headers['X-Twitter-Client'] = client
        self._request_headers['X-Twitter-Client-URL'] = url
        self._request_headers['X-Twitter-Client-Version'] = version

    def setSource(self, source):
        '''
        Suggest the "from source" value to be displayed on the Twitter web site.

        The value of the 'source' parameter must be first recognized by
        the Twitter server.  New source values are authorized on a case by
        case basis by the Twitter development team.

        Args:
            source:
                The source name as a string.  Will be sent to the server as
                the 'source' parameter.
        '''
        self._default_params['source'] = source

    def getRateLimitStatus(self):
        '''
        Fetch the rate limit status for the currently authorized user.

        Returns:
            A dictionary containing the time the limit will reset (reset_time),
            the number of remaining hits allowed before the reset (remaining_hits),
            the number of hits allowed in a 60-minute period (hourly_limit), and
            the time of the reset in seconds since The Epoch (reset_time_in_seconds).
        '''
        url  = '%s/account/rate_limit_status.json' % self.base_url
        json = self._fetchUrl(url, **{'account_specific': True})
        data = simplejson.loads(json)
        self._checkForTwitterError(data)
        return data

    def maximumHitFrequency(self):
        '''
        Determines the minimum number of seconds that a program must wait
        before hitting the server again without exceeding the rate_limit
        imposed for the currently authenticated user.

        Returns:
            The minimum second interval that a program must use so as to not
            exceed the rate_limit imposed for the user.
        '''
        rate_status = self.getRateLimitStatus()
        reset_time  = rate_status.get('reset_time', None)
        limit       = rate_status.get('remaining_hits', None)
        if reset_time:
            # Put the reset time into a datetime object.
            reset = datetime.datetime(*rfc822.parsedate(reset_time)[:7])
            # Find the difference in time between now and the reset time + 1 hour.
            delta = reset + datetime.timedelta(hours=1) - datetime.datetime.utcnow()
            if not limit:
                return int(delta.seconds)
            # Determine the minimum number of seconds allowed as a regular interval.
            max_frequency = int(delta.seconds / limit) + 1
            # Return the number of seconds.
            return max_frequency
        return 60

    def _buildUrl(self, url, path_elements=None, extra_params=None):
        # Break url into consituent parts.
        (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
        # Add any additional path elements to the path.
        if path_elements:
            # Filter out the path elements that have a value of None.
            p = [i for i in path_elements if i]
            if not path.endswith('/'):
                path += '/'
            path += '/'.join(p)
        # Add any additional query parameters to the query string.
        if extra_params and len(extra_params) > 0:
            extra_query = self._encodeParameters(extra_params)
            # Add it to the existing query.
            if query:
                query += '&' + extra_query
            else:
                query = extra_query
        # Return the rebuilt URL.
        return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))

    def _initializeRequestHeaders(self, request_headers):
        if request_headers:
            self._request_headers = request_headers
        else:
            self._request_headers = {}

    def _initializeUserAgent(self):
        user_agent = 'Python-urllib/%s (python-twitter/%s)' % \
            (self._urllib.__version__, __version__)
        self.setUserAgent(user_agent)

    def _initializeDefaultParameters(self):
        self._default_params = {}

    def _decompressGzippedResponse(self, response):
        raw_data = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            url_data = gzip.GzipFile(fileobj=StringIO.StringIO(raw_data)).read()
        else:
            url_data = raw_data
        return url_data

    def _encode(self, s):
        if self._input_encoding:
            return unicode(s, self._input_encoding).encode('utf-8')
        else:
            return unicode(s).encode('utf-8')

    def _encodeParameters(self, parameters):
        '''
        Return a string in key=value&key=value form

        Values of None are not included in the output string.

        Args:
            parameters:
                A dict of (key, value) tuples, where value is encoded as
                specified by self._encoding

        Returns:
            A URL-encoded string in "key=value&key=value" form
        '''
        if parameters is None:
            return None
        else:
            return urllib.urlencode(dict([(k, self._encode(v)) for k, v in parameters.items() if v is not None]))

    def _encodePostData(self, post_data):
        '''
        Return a string in key=value&key=value form

        Values are assumed to be encoded in the format specified by self._encoding,
        and are subsequently URL encoded.

        Args:
            post_data:
                A dict of (key, value) tuples, where value is encoded as
                specified by self._encoding

        Returns:
            A URL-encoded string in "key=value&key=value" form
        '''
        if post_data is None:
            return None
        else:
            return urllib.urlencode(dict([(k, self._encode(v)) for k, v in post_data.items()]))

    def _checkForTwitterError(self, data):
        """
        Raises a TwitterError if twitter returns an error message.

        Args:
            data:
                A python dict created from the Twitter json response

        Raises:
            TwitterError wrapping the twitter error message if one exists.
        """
        # Twitter errors are relatively unlikely, so it is faster
        # to check first, rather than try and catch the exception.
        if 'error' in data:
            raise TwitterError(data['error'])
        if data.has_key('next_cursor'):
                self.next_cursor = data['next_cursor']
        if data.has_key('previous_cursor'):
                self.previous_cursor = data['previous_cursor']

    def _fetchUrl(self,
        url,
        post_data=None,
        parameters=None,
        use_gzip_compression=None,
        **kw):
        '''
        Fetch a URL, optionally caching for a specified time.

        Args:
            url:
                The URL to retrieve
            post_data:
                A dict of (str, unicode) key/value pairs.
                If set, POST will be used.
            parameters:
                A dict whose key/value pairs should encoded and added
                to the query string. [Optional]
            use_gzip_compression:
                If True, tells the server to gzip-compress the response.
                It does not apply to POST requests.
                Defaults to None, which will get the value to use from
                the instance variable self._use_gzip [Optional]
            **kw:
                Dict of keyword arguments.
                Accepts:
                    'cache_timeout':
                        A per-call override on the default cache timeout.  Defaults
                        to the class instances self._cache_timeout value if omitted.
                    'account_specific':
                        Indicate if the call is specific to the given account.
                        If yes, an account-specific directory will be used.  Defaults
                        to False.
                    'attempt_number':
                        Integer which defaults to 0.  Used to retry "over capacity"
                        failures.

        Returns:
            A string containing the body of the response.
        '''
        cache_timeout = kw.get('cache_timeout', self._cache_timeout)
        account_specific = kw.get('account_specific', False)
        #print self.screen_name
        #if not cache_timeout:
        #    print '[%s][twitterlib] caching disabled for url %s' % (self.screen_name, url)

        # Build the extra parameters dict.
        extra_params = {}
        if self._default_params:
            extra_params.update(self._default_params)
        if parameters:
            extra_params.update(parameters)

        if post_data:
            http_method = 'POST'
        else:
            http_method = 'GET'

        if self._debugHTTP:
            _debug = 1
        else:
            _debug = 0

        http_handler  = self._urllib.HTTPHandler(debuglevel=_debug)
        https_handler = self._urllib.HTTPSHandler(debuglevel=_debug)

        #opener = register_openers()
        opener = self._urllib.OpenerDirector()
        opener.add_handler(http_handler)
        opener.add_handler(https_handler)

        if use_gzip_compression is None:
            use_gzip = self._use_gzip
        else:
            use_gzip = use_gzip_compression

        # Set up compression
        if use_gzip and not post_data:
            opener.addheaders.append(('Accept-Encoding', 'gzip'))

        if self._oauth_consumer is not None:
            if post_data and http_method == 'POST':
                parameters = post_data.copy()

            req = oauth.Request.from_consumer_and_token(
                self._oauth_consumer,
                token=self._oauth_token,
                http_method=http_method,
                http_url=url,
                parameters=parameters
            )

            req.sign_request(self._signature_method_hmac_sha1, self._oauth_consumer, self._oauth_token)

            headers = req.to_header()
            #print dir(req)
            #for k in req:
            #    print k,req[k]

            if http_method == 'POST':
                encoded_post_data = req.to_postdata()
                #print 'POST %s' % encoded_post_data
            else:
                encoded_post_data = None
                url = req.to_url()
        else:
            url = self._buildUrl(url, extra_params=extra_params)
            encoded_post_data = self._encodePostData(post_data)

        # FAILED ATTEMPT TO GET MULTI-MIME PART UPLOADING WORKING :( 2011-01-30 -JayT
        # Open and return the URL immediately if we're not going to cache
        #if kw.get('image_url', False):
        #    # If the headers have been included in keywords, then do a special
        #    # kind of request (the only reason this should be happening would
        #    # be when an image or other binary file is going to be uploaded).
        #    params = []
        #    for k in req:
        #        params.append((k, req[k]))
        #    data = wget(kw['image_url'])
        #    #params.append(('image', urllib2.urlopen(wget_opener(kw['image_url']).open(kw['image_url']))))
        #    #params.append(('image', data))
        #    print url
        #    datagen, headers = multipart_encode({'image': data})#params)
        #    opener.addheaders.append(('Content-Type', headers['Content-Type']))
        #    opener.addheaders.append(('Content-Length', headers['Content-Length']))
        #    opener.addheaders.append(('Authorization', encoded_post_data.replace('&', ',\n')))
        #    #headers['Authorization'] = encoded_post_data
        #    #request = urllib2.Request(url + '' + '', datagen, headers)
        #    urllib2.install_opener(opener)
        #    request = urllib2.Request(url, datagen, headers)#urllib2.urlopen(request)
        #    response = urllib2.urlopen(request)
        #    url_data = response.read() #self._decompressGzippedResponse(response)
        #    print url_data
        #    #opener.close()
        #elif encoded_post_data or no_cache or not self._cache or not self._cache_timeout:
        if encoded_post_data or not self._cache or not cache_timeout:
            try_number = 0
            while try_number < 2:
                try_number += 1
                try:
                    response = opener.open(url, encoded_post_data)
                    url_data = self._decompressGzippedResponse(response)
                    opener.close()
                    break
                except IOError, e:
                    print 'some kind of transport urllib2 error (ioerror), continuing on..'
                    if try_number >= 1:
                        raise e
                    continue
                except httplib.BadStatusLine, e:
                    print 'some kind of transport urllib2 error (badstatusline), continuing on..'
                    if try_number >= 1:
                        raise e
                    continue
        else:
            # Unique keys are a combination of the url and the oAuth Consumer Key
            #if self._consumer_key:
            #    key = self._consumer_key + ':' + url
            #else:
            key = url
            # See if it has been cached before
            last_cached = self._cache.getCachedTime(key, account_specific)
            # If the cached version is outdated then fetch another and store it
            #print cache_timeout
            if not last_cached or time.time() >= last_cached + cache_timeout:
                try_number = 0
                while try_number < 2:
                    try_number += 1
                    try:
                        response = opener.open(url, encoded_post_data)
                        url_data = self._decompressGzippedResponse(response)
                        opener.close()
                        break
                    except IOError, e:
                        print 'some kind of transport urllib2 error (ioerror), continuing on..'
                        if try_number >= 1:
                            raise e
                        continue
                    except httplib.BadStatusLine, e:
                        print 'some kind of transport urllib2 error (badstatusline), continuing on..'
                        if try_number >= 1:
                            raise e
                        continue
#                    except urllib2.URLError, e:
#                        print e
#                        print 'continuing on..'
#                        continue
#                    except urllib2.SSLError, e:
#                        print e
#                        print 'continuing on..'
#                        continue
                self._cache.set(key, url_data, account_specific)
            else:
                #print 'found in cache! ct=%s ... url= %s' % (cache_timeout, url)
                #print 'secs remaining was %s' % (time.time() - (last_cached + cache_timeout))
                url_data = self._cache.get(key, account_specific)
        # Always return the latest version
        #print url_data + '\n\n'
        if over_capacity_re.search(url_data):
            # Allow up to N retries for over capacity messages.
            if not kw.has_key('attempt_number'):
                kw['attempt_number'] = 0
            if kw['attempt_number'] > 2:
                raise TwitterError('Twitter is over capacity right now.')
            # Increment attempt count.
            kw['attempt_number'] += 1
            # Retry.
            return self._fetchUrl(
                url,
                post_data=post_data,
                parameters=parameters,
                use_gzip_compression=use_gzip_compression,
                **kw)
        #print url_data
        try:
            simplejson.loads(url_data)
        except ValueError:
            print 'Yikes, failed to parse this to json:\n%s\n--------------------------------------------' % url_data
        return url_data

over_capacity_re = re.compile('<title>Twitter \/ Over capacity</title>', re.M)

class _FileCacheError(Exception):
    '''Base exception class for FileCache related errors'''

class _FileCache(object):

    DEPTH = 3

    def __init__(self, root_directory=None, screen_name=''):
        self._screen_name = screen_name
        self._initializeRootDirectory(root_directory)

    def get(self, key, account_specific=False):
        key = self._cleanKey(key)
        path = self._getPath(key, account_specific)
        if os.path.exists(path):
            return open(path).read()
        else:
            return None

    def set(self, key, data, account_specific=False):
       key = self._cleanKey(key)
       path = self._getPath(key, account_specific)
       directory = os.path.dirname(path)
       if not os.path.exists(directory):
           os.makedirs(directory)
       if not os.path.isdir(directory):
           raise _FileCacheError('%s exists but is not a directory' % directory)
       temp_fd, temp_path = tempfile.mkstemp()
       temp_fp = os.fdopen(temp_fd, 'w')
       temp_fp.write(data)
       temp_fp.close()
       if not path.startswith(self._root_directory):
           raise _FileCacheError('%s does not appear to live under %s' %
               (path, self._root_directory))
       if os.path.exists(path):
           os.remove(path)
       os.rename(temp_path, path)

    def remove(self, key, account_specific=False):
       key = self._cleanKey(key)
       path = self._getPath(key, account_specific)
       if not path.startswith(self._root_directory):
           raise _FileCacheError('%s does not appear to live under %s' %
               (path, self._root_directory ))
       if os.path.exists(path):
           os.remove(path)

    def getCachedTime(self, key, account_specific=False):
        key = self._cleanKey(key)
        #print '[DEBUG] %s' % key
        path = self._getPath(key, account_specific)
        if os.path.exists(path):
            return os.path.getmtime(path)
        else:
            return None

    def _cleanKey(self, key):
        """Remove oauth parameters since they don't change query output."""
        qmark_idx = key.find('?') + 1
        parsed = urlparse.parse_qs(key[qmark_idx:], keep_blank_values=False)
        cleaned = []
        for k in parsed:
            if k[0:6].lower() != 'oauth_':
                cleaned.append('%s=%s' % (k, parsed[k][0]))
        return '%s%s' % (key[0:qmark_idx], '&'.join(cleaned))

    def _getPath(self, key, account_specific):
        key = self._cleanKey(key)
        try:
            hashed_key = md5(key).hexdigest()
        except TypeError:
            hashed_key = md5.new(key).hexdigest()

        if account_specific:
            root_dir = self._account_root_directory
        else:
            root_dir = self._root_directory

        return os.path.join(
            root_dir,
            self._getPrefix(hashed_key),
            hashed_key)

    def _getPrefix(self, hashed_key):
        return os.path.sep.join(hashed_key[0:_FileCache.DEPTH])

    def _getUsername(self):
        '''Attempt to find the username in a cross-platform fashion.'''
        try:
            return os.getenv('USER') or \
                os.getenv('LOGNAME') or \
                os.getenv('USERNAME') or \
                os.getlogin() or \
                'nobody'
        except (IOError, OSError), e:
            return 'nobody'

    def _getTmpCachePath(self):
        username = self._getUsername()
        cache_directory = 'python.cache_' + username
        return os.path.join(tempfile.gettempdir(), cache_directory)

    def _initializeRootDirectory(self, root_directory):
        if not root_directory:
            root_directory = self._getTmpCachePath()

        self._root_directory = os.path.abspath(root_directory)
        if not os.path.exists(self._root_directory):
            os.mkdir(self._root_directory)
        if not os.path.isdir(self._root_directory):
            raise _FileCacheError('%s exists but is not a directory' % self._root_directory)

        self._account_root_directory = os.path.join(self._root_directory, self._screen_name)
        if not os.path.exists(self._account_root_directory):
            os.mkdir(self._account_root_directory)
        if not os.path.isdir(self._account_root_directory):
            raise _FileCacheError('%s exists but is not a directory' % self._account_root_directory)

