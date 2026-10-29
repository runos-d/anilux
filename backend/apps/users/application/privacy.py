"""Shared privacy decisions for projections and media access."""
from django.db.models import Q


def prepare_privacy(owners, viewer, fields):
    """Prime contact decisions once for an entire serialized page."""
    from django.db.models import prefetch_related_objects
    owners = list(owners)
    if not owners:
        return owners
    prefetch_related_objects(owners, 'privacy_settings', 'profile_settings', 'settings')
    if not viewer or not viewer.is_authenticated:
        return owners
    policies = {
        'who_can_see_email': {'email'}, 'who_can_see_phone': {'phone_number'},
        'who_can_see_last_seen': {'last_login', 'last_seen'},
        'who_can_see_profile_photo': {'avatar', 'avatar_url', 'author_avatar', 'user_avatar'},
    }
    targets = {owner.pk for owner in owners if owner.pk != viewer.pk and any(
        set(fields) & names and getattr(getattr(owner, 'privacy_settings', None), policy,
            'everyone' if policy == 'who_can_see_profile_photo' else 'contacts') == 'contacts'
        for policy, names in policies.items())}
    contacts = set()
    if targets:
        from apps.social.infrastructure.models.social import PrivateChat
        for first, second in PrivateChat.objects.filter(
            Q(user1_id=viewer.pk, user2_id__in=targets) | Q(user2_id=viewer.pk, user1_id__in=targets)
        ).values_list('user1_id', 'user2_id'):
            contacts.add(second if first == viewer.pk else first)
    for owner in owners:
        if owner.pk in targets:
            owner._privacy_contacts = {viewer.pk: owner.pk in contacts}
    return owners


def can_view_field(owner, viewer, field):
    if viewer and viewer.is_authenticated and viewer.pk == owner.pk:
        return True
    privacy = getattr(owner, 'privacy_settings', None)
    policy = getattr(privacy, field, 'everyone' if field == 'who_can_see_profile_photo' else 'contacts')
    if policy == 'everyone':
        return True
    if policy != 'contacts' or not viewer or not viewer.is_authenticated:
        return False
    from apps.social.infrastructure.models.social import PrivateChat
    contacts = getattr(owner, '_privacy_contacts', {})
    if viewer.pk not in contacts:
        contacts[viewer.pk] = PrivateChat.objects.filter(Q(user1=owner, user2=viewer) | Q(user2=owner, user1=viewer)).exists()
        owner._privacy_contacts = contacts
    return contacts[viewer.pk]


def project_user(data, owner, viewer):
    for policy, fields in {
        'who_can_see_email': ('email',),
        'who_can_see_phone': ('phone_number',),
        'who_can_see_last_seen': ('last_login', 'last_seen'),
        'who_can_see_profile_photo': ('avatar', 'avatar_url', 'author_avatar', 'user_avatar'),
    }.items():
        if any(field in data for field in fields) and not can_view_field(owner, viewer, policy):
            for field in fields:
                if field in data:
                    data[field] = None
    profile = getattr(owner, 'profile_settings', None)
    account = getattr(owner, 'settings', None)
    if ((profile and not profile.show_online_status) or (account and not account.show_online_status)) and (not viewer or viewer.pk != owner.pk):
        data['is_online'] = False
    return data


def can_forward_message(message, user):
    if message.sender_id == user.pk:
        return True
    privacy = getattr(message.sender, 'privacy_settings', None)
    return privacy is None or privacy.allow_message_forwarding
