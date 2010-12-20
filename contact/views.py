#r!/usr/bin/env python
#
# Copyright 2010 Google Inc.
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

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect

from forms import *

#@cache_page(60*5)
def static(request, template):
  return render_to_response(template, RequestContext(request,{}))

def contact(request):
  if request.method == 'POST':
    form = ContactForm(request.POST)
    if form.is_valid():
      subject = form.cleaned_data['subject']
      sender = form.cleaned_data['sender']
      message = 'The following feedback was submitted from %s \n\n' % sender
      message += form.cleaned_data['message']
      cc_myself = form.cleaned_data['cc_myself']

      recipients = settings.CONTACT_EMAILS
      if cc_myself:
        recipients.append(sender)

      from django.core.mail import send_mail
      send_mail(subject, message, sender, recipients)

      return HttpResponseRedirect('/contact/thanks/') # Redirect after POST
  else:
    form = ContactForm() # An unbound form

  return render_to_response('contact.html', {
    'form': form,
  })

