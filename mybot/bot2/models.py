from django.db import models
from django.utils import timezone

class TeamsUser(models.Model):
    """Teams user who has subscribed to the bot"""
    user_id = models.CharField(max_length=255, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, blank=True, null=True)
    tenant_id = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    conversation_reference = models.TextField(blank=True, null=True)  # Store conversation reference for proactive messaging
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user_id})"

class UserResponse(models.Model):
    """User's response to hourly questions"""
    user = models.ForeignKey(TeamsUser, on_delete=models.CASCADE, related_name='responses')
    question_time = models.TimeField()  # Time when question was asked (9:00, 10:00, etc.)
    question_date = models.DateField()  # Date when question was asked
    response_text = models.TextField()
    response_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'question_time', 'question_date']
        ordering = ['-question_date', '-question_time']

    def __str__(self):
        return f"{self.user.name} - {self.question_date} {self.question_time} - {self.response_text[:50]}"
