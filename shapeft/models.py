import random
import md5

from django.db import models
from ft_auth.models import OAuthAccessToken


STATUS_CODES = {
 1 : 'In Queue (%s ahead of you)',
 2 : 'Initial Processing',
 3 : 'Importing into Fusion Tables',
 4 : 'Complete',
 6 : 'Error'
}


class shapeUpload(models.Model):
  """An upload -- includes location of initial shape, processing status, etc"""
  auth_token = models.ForeignKey(OAuthAccessToken)
  uid = models.CharField(max_length=250)
  shapefile = models.CharField(max_length=250)
  status = models.IntegerField()
  status_msg = models.CharField(max_length=250,null=True)
  total_rows = models.IntegerField(null=True)
  rows_processed = models.IntegerField(null=True)
  rows_imported = models.IntegerField(null=True)
  ft_table_id = models.IntegerField(null=True)
  uploaded = models.DateTimeField(auto_now_add=True)
  create_simplify = models.BooleanField(default=True)
  create_centroid = models.BooleanField(default=True)
  create_centroid_poly = models.BooleanField(default=False)

  def get_title(self):
    return self.shapefile.split('/')[-1]

  def get_status(self):
    status = STATUS_CODES[self.status]
    if self.status == 1:
      queue_length = shapeUpload.objects.filter(status=1).count()
      status = status % (queue_length - 1)
    return status

  def save(self):
    salt = 'shapebar'
    if not self.id:
      super(shapeUpload, self).save()
    hash = md5.new(salt + str(self.id))
    self.uid = hash.hexdigest()
    super(shapeUpload, self).save()
