#!/usr/bin/env python
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

import math
import sys
import os
import time
import urllib


if len(sys.argv) < 3:
  print "Usage: %s <path to settings module> <settings module name>" % sys.argv[0]
  sys.exit()
class KeyboardException: pass
sys.path = [sys.argv[1]] + sys.path
os.environ['DJANGO_SETTINGS_MODULE'] = sys.argv[2]

from shapeft.models import *
from shapeft.views import *

def run():
  while True:
    uploads = shapeUpload.objects.filter(status=1)
    for upload in uploads:
      print 'working oni %d:  %s' % (upload.id, upload.shapefile)
      try:
        import_from_shape(upload)
        print "Finished with %s" % upload.shapefile
      except Exception, E:
        print "Error occurred (%s)" % E
        upload.status = 6
        upload.status_msg = str(E)
        upload.save()
    time.sleep(8)

if __name__ == "__main__":
  run()
