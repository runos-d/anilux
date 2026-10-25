from django.db import models
from django.db.models import Q
from .chat_cascade import chat_cascade


class Conversation(models.Model):
    id = models.BigAutoField(primary_key=True)
    private_chat = models.OneToOneField('social.PrivateChat', null=True, blank=True,
                                      on_delete=chat_cascade, related_name='conversation')
    group_chat = models.OneToOneField('social.GroupChat', null=True, blank=True,
                                    on_delete=chat_cascade, related_name='conversation')
    next_message_seq = models.PositiveBigIntegerField(default=0)
    event_seq = models.PositiveBigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(
            condition=(Q(private_chat__isnull=False, group_chat__isnull=True) |
                       Q(private_chat__isnull=True, group_chat__isnull=False)),
            name='conversation_exactly_one_chat')]

    @property
    def chat(self):
        return self.private_chat if self.private_chat_id else self.group_chat

    @property
    def kind(self):
        return 'private' if self.private_chat_id else 'group'


class ChatEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(Conversation, null=True, on_delete=models.SET_NULL, related_name='events')
    sequence = models.PositiveBigIntegerField()
    kind = models.CharField(max_length=40)
    payload = models.JSONField(default=dict)
    recipients = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['conversation', 'sequence'], name='chat_event_sequence_unique')]
        indexes = [models.Index(fields=['delivered_at', 'id'], name='chat_event_pending_idx')]
        ordering = ['sequence']


class ConversationUserState(models.Model):
    id = models.BigAutoField(primary_key=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='user_states')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    hidden = models.BooleanField(default=False)
    cleared_through_seq = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['conversation', 'user'], name='conversation_user_unique')]
