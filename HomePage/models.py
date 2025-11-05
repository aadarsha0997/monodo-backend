from django.db import models

# Create your models here.

class HomeCart(models.Model):
    image=models.ImageField( upload_to='images/homepage')
    location=models.CharField( max_length=50)
    price=models.IntegerField()
    rating=models.FloatField()
    reviews=models.IntegerField()
    

    def __str__(self):
        return f"{self.location}"

    class Meta:
        verbose_name_plural='Homepage_ImageDB'

class reveiw_cart(models.Model):
    pass
    
class User(models.Model):
    user_name=models.CharField( max_length=50)
    phone_number=models.BigIntegerField()
    balance=models.IntegerField()
    # withdraw_password=models.IntegerField()
    # login_password=models.CharField(max_length=50)
    # invitation_code=models.CharField( max_length=50)
    # review_cart=models.ForeignKey("app.Model", on_delete=models.CASCADE)


    class Meta:
        verbose_name_plural='UserDB'
    
    def __str__(self):
        return f"{self.user_name}"
