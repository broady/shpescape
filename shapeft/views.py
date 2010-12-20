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
import os
import random
import time

from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
from django.contrib.gis.geos import fromstr, LineString
from django.contrib.gis.models import SpatialRefSys
from django.contrib.gis.gdal import DataSource, OGRGeometry
from django.utils.datastructures import SortedDict

import simplejson

from shapes.forms import UploadForm
from ft_auth.views import *
from shapeft.models import shapeUpload

#@cache_page(60*5)
def static(request, template):
  if not template:
    template = "index.html"
  return render_to_response(template, RequestContext(request,{}))

def generic_import(request):
  """
  accept an uploaded file and create associated shapeUpload obj
  """
  token = get_token(request)
  if not token:
    return HttpResponseRedirect('/auth/FTVerify')
  if request.method == 'POST':
    form = UploadForm(request.POST, request.FILES)
    if form.is_valid():
      form.handle(request.FILES['file_obj'])
      create_simplify = request.POST.get('create_simplify', False);
      create_centroid = request.POST.get('create_centroid', False);
      create_centroid_poly = request.POST.get('create_centroid_poly', False);

      #save form info in a model, and run from cron
      uids = []
      for shapefile in form.shapefiles:
        upload = shapeUpload()
        upload.auth_token = token
        upload.shapefile = shapefile
        upload.status = 1
        upload.save()
        upload.create_simplify = bool(create_simplify)
        upload.create_centroid = bool(create_centroid)
        upload.create_centroid_poly = bool(create_centroid_poly)
        uids.append(upload.uid)
      url = '/uploads/%s/' % 'g'.join(uids)
      return HttpResponseRedirect(url)
  else:
    form = UploadForm()
  return render_to_response('upload.html', RequestContext(request,{
    'form': form}))

def upload_detail(request, upload_ids):
  """
  display status of one or more shapeUploads
  """
  uids = upload_ids.split('g')
  uploads = shapeUpload.objects.filter(uid__in=uids).order_by('id')
  #upload = get_object_or_404(shapeUpload, id=upload_id)
  return render_to_response('upload_detail.html', RequestContext(request,{
    'uploads': uploads}))


def import_from_shape(upload,
                      start_row=0,
                      max_rows=200000,
                      create_int_style_cols=True):
  """
  a shapeUpload object
  max_rows - any more than this is ignored
  centroid - if it's a (multi)polygon, should we also create a geometry_centroid field
  """

  upload.status = 2 #set this right away so it doesn't get reprocessed
  upload.save()
  ds = DataSource(upload.shapefile)
  layer = ds[0]
  fields = layer.fields

  num_features = len(layer)
  #set max # of _style features
  max_distinct_style_vals = max(min(num_features / 100, 50),10)
  print 'there are %d features' % num_features
  upload.total_rows = num_features
  if not num_features:
    print 'no rows, returning'
    upload.status = 6
    upload.save()
    return

  rows = []
  #get field types
  field_map = {
       'OFTString':'STRING',
       'OFTReal':'NUMBER',
       'OFTInteger':'NUMBER',
       'OFTDate':'DATETIME'
  }
  field_types = [field_map[f.__name__] for f in layer.field_types]
  field_layers = layer.fields

  #insert geometry layers first
  field_layers.insert(0,'geometry')
  field_types.insert(0,'LOCATION')
  field_layers.insert(1,'geometry_vertex_count')
  field_types.insert(1,'NUMBER')


  if upload.create_simplify:
    field_layers.insert(0,'geometry_simplified')
    field_types.insert(0,'LOCATION')
    field_layers.insert(1,'geometry_simplified_vertex_count')
    field_types.insert(1,'NUMBER')

  #use sorted dict so we can ensure table has geom columns upfront
  field_dict = SortedDict(zip(field_layers, field_types))

  #set up extra fields if creating int/style cols
  if create_int_style_cols:
    int_style_dict = {}
    for field,field_type in field_dict.items():
      if field_type == 'STRING':
        field_dict[field + '_ft_style'] = 'NUMBER'
        int_style_dict[field] = {}
    print field_dict

  #add some custom import fields
  field_dict['import_notes'] = 'STRING'

  print 'FIELD DICT', field_dict
  print 'starting to process'
  for i, feat in enumerate(layer):
    if i > max_rows:
      continue
    if start_row and i < start_row:
      continue
    upload.rows_processed = i + 1
    if not i % ((num_features / 50) or 5):
      print upload.rows_processed,'rp'
      upload.save()
    upload.save()
    rd = {}
    #geom = fromstr(feat.geom.wkt,srid=srid)
    if layer.srs:
      try:
        geom = OGRGeometry(feat.geom.wkt, layer.srs.proj4)
        geom.transform(4326)
      except Exception, e:
        print 'FAIL GEOM'
        print e,
        geom = None
    else:
      geom = OGRGeometry(feat.geom.wkt)


    if geom:
      geom = fromstr(geom.wkt)
      #create optional centroid for polys
      if upload.create_centroid and 'oly' in geom.geom_type:
        field_dict['geometry_pos'] = 'LOCATION'
        rd['geometry_pos'] = geom.point_on_surface.kml

      if upload.create_centroid_poly and 'oly' in geom.geom_type:
        field_dict['geometry_pos_poly_2'] = 'LOCATION'
        field_dict['geometry_pos_poly_3'] = 'LOCATION'

        rd['geometry_pos_poly_2'] = geom.point_on_surface.buffer(.0001,10).kml
        rd['geometry_pos_poly_3'] = geom.point_on_surface.buffer(.0005,10).kml

      #if it's > 1M characters, we need to simplify it for FT
      simplify_tolerance = .0001
      while len(geom.kml) > 1000000:
        geom = geom.simplify(simplify_tolerance)
        print 'simplified to %f' % simplify_tolerance
        rd['import_notes'] = 'simplified to %d DD' % simplify_tolerance
        simplify_tolerance = simplify_tolerance * 1.5

      if not geom.valid:
        rd['import_notes'] = '<br>Geometry not valid'

      kml = geom.kml
      rd['geometry'] = kml
      rd['geometry_vertex_count'] = geom.num_coords

      if upload.create_simplify and not 'oint' in geom.geom_type:
        amt = .002
        if 'oly' in geom.geom_type:
          buffer_geom = geom.buffer(amt)
          buffer_geom = buffer_geom.buffer(amt * -1)
          simple_geom = buffer_geom.simplify(amt)
        else:
          simple_geom = geom.simplify(amt)

        rd['geometry_simplified'] = simple_geom.kml
        rd['geometry_simplified_vertex_count'] = simple_geom.num_coords

    for f in fields:
      val = feat.get(f)
      #make sure we have proper null type for diff fields
      if val == '<Null>':
        continue
      if not val:
        continue

      if field_dict[f] == 'DATETIME':
        val = val.isoformat().split('T')[0]

      if field_dict[f] == 'STRING' \
        and create_int_style_cols \
        and field_dict.has_key(f + '_ft_style'):

        #check to see if we have a number for this yet
        try:
          rd[f + '_ft_style'] = int_style_dict[f][val]
        except:
          int_style_dict[f][val] = len(int_style_dict[f])
          rd[f + '_ft_style'] = int_style_dict[f][val]
        #however if we have too many distinct vals, let's just not do this anymore
        if len(int_style_dict[f]) > max_distinct_style_vals:
          print 'DELETING FD %s' % f
          del field_dict[f + '_ft_style']
          del rd[f + '_ft_style']
          #sucks, but now we should just remove all these fields from previous rows
          for srow in rows:
            try:del srow[f + '_ft_style']
            except:
              pass #probably this was a null value?

      rd[f] = val
    rows.append(rd)
    #let's process 10k rows at a time.. not keep everything in memory
    if len(rows) > 10000:
      uploadRows(upload, field_dict, rows)
      rows = []

  uploadRows(upload, field_dict, rows)

def uploadRows(upload, field_dict, rows):
  if not upload.ft_table_id:
    upload = createTable(upload, field_dict)
  upload.status = 3
  upload.save()
  print 'inserting %d rows' % len(rows)
  insertData(upload, field_dict, rows)
  upload.status = 4
  upload.save()

def insertSql(client, sql, attempt_no=0):
  try:resp = client.query(sql)
  except:
    print 'unable to query sql %s' % sql
    resp = client.query(sql)
  print resp[:50]
  if 'Unable' in resp:
    if attempt_no > 3:
      return 'Error - failed after 3 attempts' + resp
    #print sql
    print resp
    time.sleep(1)
    print 'len: %d, attempt: %d' % (len(sql), attempt_no)
    insertSql(client, sql, attempt_no + 1)
  return resp


def getClient(upload):
  ftClient = OAuthFTClient(
    FT_OAUTH['key'],
    FT_OAUTH['secret'],
    upload.auth_token.ft_token,
    upload.auth_token.ft_token_secret)
  print 'client created'
  return ftClient

def createTable(upload, field_dict):
  ftClient = getClient(upload)
  table_dictionary = {upload.get_title() : field_dict}
  results = ftClient.query(SQL().createTable(table_dictionary))
  table_id = results.split("\n")[1]
  print 'new table: %s' % results
  upload.ft_table_id = table_id
  upload.save()
  return upload

def insertData(upload, field_dict, rows):
  ftClient = getClient(upload)
  #insert rows
  sql = []
  sql_len = 0
  for i, row in enumerate(rows):
    upload.rows_imported = i + 1
    if sql_len > 500000 or len(sql) > 100: # max upload is 1MB?
      insertSql(ftClient, ';'.join(sql))
      sql = []
      sql_len = 0
      upload.save()
    try:
      insert_statement = SQL().insert(upload.ft_table_id, row)
    except Exception, e:
      print 'FAIL SQL', row
      print e
      continue
    sql.append(insert_statement)
    sql_len += len( insert_statement)

  insertSql(ftClient, ';'.join(sql))
  upload.save()
