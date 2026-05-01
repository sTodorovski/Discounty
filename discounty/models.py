from django.db import models

# Create your models here.
class Market(models.Model):
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to='images/')
    description = models.TextField(default='')
    location_city = models.TextField(blank=True, null=True)
    location_market = models.TextField(blank=True, null=True)
    last_updated = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.IntegerField()
    unit_price = models.FloatField(blank=True, null=True)
    description = models.TextField()
    availability = models.BooleanField()
    regular_price = models.IntegerField()
    discount_price = models.IntegerField(blank=True, null=True)
    discount_percentage = models.FloatField(blank=True, null=True)
    discount_type = models.CharField(max_length=200, blank=True, null=True)
    discount_date_from = models.DateField(blank=True, null=True)
    discount_date_to = models.DateField(blank=True, null=True)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, default=3)

    def __str__(self):
        return self.name