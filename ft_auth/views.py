#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import random
from datetime import datetime

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.template import RequestContext
from django.conf import settings

from ftlibrary.authorization.oauth import OAuth
from ftlibrary.ftclient import OAuthFTClient
from ftlibrary.sql.sqlbuilder import SQL

import ftlibrary.oauth2 as oauth # httplib2 is required for this to work on AppEngine

from models import *

FT_OAUTH = {
   'key': settings.FT_DOMAIN,
   'secret': settings.FT_DOMAIN_SECRET,
   'domain': settings.FT_DOMAIN
}


def get_token(request):
  """
  see if we have an oauth token for them, based on their ip and session key
  """
  try:
    ft_session = request.session['ft_token']
    token = OAuthAccessToken.objects.get(session_key=ft_session)
    # invalidate any token > 24 hours old
    now = datetime.now()
    diff = now - token.created
    if diff.days:
      token.delete()
      return False
    # TODO check ip address matches
    #oauthorize
    return token
  except KeyError:
    print 'no session token..'
  except OAuthAccessToken.DoesNotExist:
    print 'no access token ...'
  return False

def create_session_key(request):
 ip = request.META['REMOTE_ADDR']
 skey = ip + str(random.random())
 return skey.replace('.','')

def FTVerify(request):
  ft_session = create_session_key(request)
  callback_url = 'http://' + request.META['HTTP_HOST'] + '/auth/FTAuthenticate'
  url,token,secret = OAuth().generateAuthorizationURL(
   consumer_key=FT_OAUTH['key'],
   consumer_secret=FT_OAUTH['secret'],
   domain=FT_OAUTH['domain'],
   callback_url=callback_url)
  #save the new token

  request_token = OAuthRequestToken(
    ft_token=token,
    ft_token_secret=secret,
    session_key=ft_session)
  request_token.save()

  #save session key
  request.session['ft_token'] = ft_session
  return HttpResponseRedirect(url)



def FTAuthenticate(request):
  #get the old token and secret
  try:
   ft_session = request.session['ft_token']
  except KeyError:
   raise Exception('should not get here ... no session key')
   HttpResponseRedirect('/FTVerify')
  request_token = OAuthRequestToken.objects.filter(session_key=ft_session)
  if not request_token:
   raise Exception('should not get here ... no token key')
   HttpResponseRedirect('/FTVerify')

  token = request_token[0].ft_token
  secret = request_token[0].ft_token_secret
  #retrieve the access token and secret, these will be used in future requests
  #so save them in the database for the user
  access_token, access_secret = OAuth().authorize(
   consumer_key=FT_OAUTH['key'],
   consumer_secret=FT_OAUTH['secret'],
   oauth_token=token,
   oauth_token_secret=secret)


  oauth_token = OAuthAccessToken(
    ft_token=access_token,
    ft_token_secret=access_secret,
    session_key=ft_session)
  oauth_token.save()
  return HttpResponseRedirect('/upload')
