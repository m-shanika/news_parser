from django.contrib import admin
from apps import models

@admin.register(models.Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", )

@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "notification_id")


@admin.register(models.NewsCPM)
class NewsCPMAdmin(admin.ModelAdmin):
    list_display = ("id", "news_id")

@admin.register(models.NewsMedia)
class NewsMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "news_id")

@admin.register(models.NewsSeller)
class NewsSellerAdmin(admin.ModelAdmin):
    list_display = ("id", "news_id")


@admin.register(models.OzonNews)
class OzonNewsAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at")