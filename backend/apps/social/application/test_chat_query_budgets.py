from django.test import TestCase

from apps.social.infrastructure.models.social import ChatMember, ChatRole, GroupChat
from apps.social.presentation.views.views_chat import managed_chat_ids
from apps.users.infrastructure.models.users import User


class ManagedChatQueryBudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="moderator", email="moderator@example.com", password="Safe-pass-1842"
        )
        owner_chat = GroupChat.objects.create(name="Owned", created_by=cls.user)
        ChatMember.objects.create(chat=owner_chat, user=cls.user)

        admin_chat = GroupChat.objects.create(name="Admin")
        ChatMember.objects.create(chat=admin_chat, user=cls.user, is_admin=True)

        role_chat = GroupChat.objects.create(name="Role")
        role = ChatRole.objects.create(
            chat=role_chat,
            name="Moderator",
            can_ban_users=True,
            created_by=cls.user,
        )
        ChatMember.objects.create(chat=role_chat, user=cls.user, role=role)

        denied_chat = GroupChat.objects.create(name="Denied")
        ChatMember.objects.create(chat=denied_chat, user=cls.user)
        cls.expected = {owner_chat.pk, admin_chat.pk, role_chat.pk}

    def test_managed_chat_ids_is_one_query(self):
        request = type("Request", (), {"user": self.user})()
        with self.assertNumQueries(1):
            actual = set(managed_chat_ids(request, "can_ban_users"))
        self.assertEqual(actual, self.expected)
