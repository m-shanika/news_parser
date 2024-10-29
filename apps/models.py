from django.db import models

class Organization(models.Model):
    supplier_id = models.TextField(verbose_name='Айди саплаера')
    validation_key = models.TextField(verbose_name='Ключ валидации')
    seller_device_id = models.TextField(verbose_name='Device id')
    access_token = models.TextField(verbose_name='Access Token')
    refresh_token = models.TextField(verbose_name='Refresh Token')

    def __str__(self):
        return f"{self.id}"

    class Meta:
        verbose_name = "Орагнизация"
        verbose_name_plural = "Организации"

class Notification(models.Model):
    notification_id = models.CharField(max_length=255, unique=True)
    text = models.TextField()
    link = models.URLField()
    received_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_id}"

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

class NewsCPM(models.Model):
    news_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    publication_date = models.DateTimeField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость Продвижение ВБ"
        verbose_name_plural = "Новости Продвижение ВБ"

class NewsMedia(models.Model):
    news_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255)
    publication_date = models.DateTimeField()
    body = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость Медиа ВБ"
        verbose_name_plural = "Новости Медиа ВБ"

class NewsSeller(models.Model):
    news_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()
    date = models.DateTimeField()  
    sent_to_telegram = models.BooleanField(default=False) 

    def __str__(self):
        return self.title


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость Seller ВБ"
        verbose_name_plural = "Новости Seller ВБ"

class OzonNews(models.Model):
    title = models.CharField(max_length=255)
    link = models.URLField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_to_telegram = models.BooleanField(default=False) 


    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Новость Ozon"
        verbose_name_plural = "Новости Ozon"