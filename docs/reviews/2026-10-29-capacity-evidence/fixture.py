import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','capacity_settings')
import django
django.setup()
from django.conf import settings
assert settings.DATABASES['default']['HOST']=='audit-mysql' and settings.DATABASES['default']['NAME']=='chat_test'
import config.urls
import json,secrets,uuid
from datetime import timedelta
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from rest_framework_simplejwt.tokens import AccessToken
from apps.users.infrastructure.models.users import User,UserSettings,UserProfileSettings,PrivacySettings,ActiveSession
from apps.anime.models import Anime
from apps.social.infrastructure.models.social import GroupChat,ChatMember,Message,Post
from apps.social.infrastructure.models.conversation import Conversation
count=int(os.environ.get('CAPACITY_USERS','6000'));assert 1<=count<=6000
room_size=int(os.environ.get('CAPACITY_ROOM_SIZE','60'));assert 1<=room_size<=6000
if User.objects.filter(username__startswith='capacity-load-').exists():raise RuntimeError('Use a clean disposable schema')
User.objects.bulk_create([User(username=f'capacity-load-{i}',email=f'capacity-load-{i}@example.test',password='!') for i in range(count)],batch_size=500)
users=list(User.objects.filter(username__startswith='capacity-load-').order_by('pk'))
UserSettings.objects.bulk_create([UserSettings(user=user) for user in users],batch_size=500)
UserProfileSettings.objects.bulk_create([UserProfileSettings(user=user) for user in users],batch_size=500)
PrivacySettings.objects.bulk_create([PrivacySettings(user=user,who_can_see_profile_photo='everyone',who_can_see_last_seen='everyone') for user in users],batch_size=500)
room_count=max(1,(count+room_size-1)//room_size)
GroupChat.objects.bulk_create([GroupChat(public_id=90000000+i,name=f'Capacity room {i}',code=str(90000000+i),created_by=users[i%count],max_members=max(200,room_size)) for i in range(room_count)],batch_size=100)
rooms=list(GroupChat.objects.filter(name__startswith='Capacity room').order_by('pk'))
ChatMember.objects.bulk_create([ChatMember(user=user,chat=rooms[i//room_size]) for i,user in enumerate(users)],batch_size=500)
Conversation.objects.bulk_create([Conversation(group_chat=room,next_message_seq=10) for room in rooms],batch_size=100)
conversations={row.group_chat_id:row for row in Conversation.objects.filter(group_chat__in=rooms)}
Message.objects.bulk_create([Message(public_id=80000000+i*10+j,chat=room,conversation=conversations[room.pk],sender=users[i*room_size],seq=j+1,
 text=f'History {j}',client_message_id=str(uuid.uuid4())) for i,room in enumerate(rooms) for j in range(10)],batch_size=500)
Anime.objects.bulk_create([Anime(title_ru=f'Нагрузочный тайтл {i}',slug=f'capacity-anime-{i}',shikimori_id=50000+i,is_available=True,has_cyrillic=True,year=2024,score=8,episodes=12) for i in range(10000)],batch_size=500)
Post.objects.bulk_create([Post(public_id=70000000+i,author=users[i%count],text=f'Capacity post {i}: '+('test ' * 30),status='published',visibility='public') for i in range(60000)],batch_size=500)
sessions=[]
for user in users:
 sessions.append(Session(session_key=secrets.token_hex(16),expire_date=timezone.now()+timedelta(hours=24),session_data=SessionStore().encode({'_auth_user_id':str(user.pk),'_auth_user_hash':user.get_session_auth_hash()})))
Session.objects.bulk_create(sessions,batch_size=500)
ActiveSession.objects.bulk_create([ActiveSession(user=user,session_key=session.session_key,ip_address='127.0.0.1',user_agent='capacity-test') for user,session in zip(users,sessions)],batch_size=500)
selectors=dict(ActiveSession.objects.filter(user__in=users).values_list('user_id','pk'))
rows=[]
for i,user in enumerate(users):
 token=AccessToken.for_user(user);token['sid']=str(selectors[user.pk]);token['ver']=user.token_version
 rows.append({'user_id':user.pk,'access':str(token),'chat_id':rooms[i//room_size].public_id})
print('TOKENS='+json.dumps({'users':rows,'rooms':room_count,'room_size':room_size,'posts':60000,'anime':10000}),flush=True)
