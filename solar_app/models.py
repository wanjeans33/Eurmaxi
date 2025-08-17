"""
Django Models for Solar Simulation App
由于这是一个计算型应用，不需要存储数据，所以这个文件基本为空
"""
from django.db import models

# 如果将来需要保存用户的模拟历史，可以在这里添加模型
# 例如：
# class SimulationHistory(models.Model):
#     created_at = models.DateTimeField(auto_now_add=True)
#     parameters = models.JSONField()
#     results = models.JSONField()
#     user_ip = models.GenericIPAddressField(null=True, blank=True)


