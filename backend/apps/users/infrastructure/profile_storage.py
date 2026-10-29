from urllib.parse import quote
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class ProfileStorage(FileSystemStorage):
    def url(self, name):
        return '/api/users/profile-media/' + quote(name, safe='/')


profile_storage = ProfileStorage()
