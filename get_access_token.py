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


import os
import sys

from wget import *

# parse_qsl moved to urlparse module in v2.6
try:
  from urlparse import parse_qsl
except:
  from cgi import parse_qsl

import oauth2 as oauth


import re
import mechanize
import cookielib

from wget import *

def login(username, password):
    login_url = 'https://twitter.com/login'
    br = mechanize.Browser()
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    resp = br.open(login_url)
    #print resp.get_data()
    br.select_form(nr=0)
    nr = 1
    while len(br.form.controls) < 2:
        br.select_form(nr=nr)
        nr += 1
    br.form['session[username_or_email]'] = username
    br.form['session[password]'] = password
    br.submit()
    return br

def set_profile_img(username, password, image_url):
    settings_url = 'http://twitter.com/settings/profile'
    br = login(username, password)
    br.open(settings_url)
    br.select_form(nr=0)
    nr = 1
    while len(br.form.controls) < 2:
        br.select_form(nr=nr)
        nr += 1
    #print br.form
    #br.form['profile_image[uploaded_data]'] = image_url[image_url.rindex('/'):]
    urllib2.install_opener(wget_opener(settings_url))
    print 'setting profile image to %s' % image_url
    br.form.add_file(urllib2.urlopen(image_url), 'image/jpg', '%s.jpg' % image_url[image_url.rindex('/'):], **{'name': 'profile_image[uploaded_data]'})
    #br.form.add_file(open('test.jpg'), 'image/jpg', 'test.jpg', **{'name': 'profile_image[uploaded_data]'})
    br.submit().get_data()

def get_twitter_pin(username, password, url):
    br = mechanize.Browser()
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    br.open(url)
    br.select_form(nr=0)
    br.form['session[username_or_email]'] = username
    br.form['session[password]'] = password
    for i in range(len(br.form.controls)):
        if br.form.controls[i].type == 'submit' and br.form.controls[i].id == 'deny':
            del br.form.controls[i]
            break
    br.submit()
    pin_re = re.compile('<div id="oauth_pin">(?P<pin>[^<]+)')
    m = re.search(pin_re, br.response().read())
    if m:
        return m.group('pin').strip()
    return ''


REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
ACCESS_TOKEN_URL  = 'https://api.twitter.com/oauth/access_token'
AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'
SIGNIN_URL        = 'https://api.twitter.com/oauth/authenticate'


def get_access_token(username, password, consumer_key, consumer_secret):
    #if consumer_key is None or consumer_secret is None:
    #    print 'You need to edit this script and provide values for the'
    #    print 'consumer_key and also consumer_secret.'
    #    print ''
    #    print 'The values you need come from Twitter - you need to register'
    #    print 'as a developer your "application".  This is needed only until'
    #    print 'Twitter finishes the idea they have of a way to allow open-source'
    #    print 'based libraries to have a token that can be used to generate a'
    #    print 'one-time use key that will allow the library to make the request'
    #    print 'on your behalf.'
    #    print ''
    #    sys.exit(1)
    signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
    oauth_consumer             = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    oauth_client               = oauth.Client(oauth_consumer)

    #print 'Requesting temp token from Twitter'
    resp, content = oauth_client.request(REQUEST_TOKEN_URL, 'GET')

    if resp['status'] != '200':
        print '[%s] Invalid response from Twitter requesting temp token: %s' % (username, resp['status'])
        raise Exception('[%s] Invalid response from Twitter requesting temp token: %s' % (username, resp['status']))
    else:
        request_token = dict(parse_qsl(content))

    #print ''
    #print 'Please visit this Twitter page and retrieve the pincode to be used'
    #print 'in the next step to obtaining an Authentication Token:'
    #print ''
    #print '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
    #print ''
    url = '%s?oauth_token=%s' % (AUTHORIZATION_URL, request_token['oauth_token'])
    ##print wget(url, 'http://www.twitter.com/', cache=False)
    pincode = get_twitter_pin(username, password, url)# raw_input('Pincode? ')

    token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
    token.set_verifier(pincode)

    #print ''
    #print 'Generating and signing request for an access token'
    #print ''
    oauth_client  = oauth.Client(oauth_consumer, token)
    resp, content = oauth_client.request(ACCESS_TOKEN_URL, method='POST', body='oauth_verifier=%s' % pincode)
    access_token  = dict(parse_qsl(content))

    if resp['status'] != '200':
        print 'The request for a Token did not succeed: %s' % resp['status']
        print resp
        print access_token
        return {}
    #else:
    #    print 'Your Twitter Access Token key: %s' % access_token['oauth_token']
    #    print '          Access Token secret: %s' % access_token['oauth_token_secret']
    return access_token

