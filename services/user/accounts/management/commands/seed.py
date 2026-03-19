from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from django.db import transaction

USER_DATA = [
    {"username": "alice", "email": "alice@example.com", "password": "password123", "bio": "Hi, I'm Alice!", "avatar": "", "location": "Wonderland"},
    {"username": "bob", "email": "bob@example.com", "password": "password123", "bio": "Bob the builder", "avatar": "", "location": "Builderland"},
    {"username": "carol", "email": "carol@example.com", "password": "password123", "bio": "Carol's adventures", "avatar": "", "location": "Adventure City"},
    {"username": "dave", "email": "dave@example.com", "password": "password123", "bio": "Dave here!", "avatar": "", "location": "Tech Town"},
    {"username": "eve", "email": "eve@example.com", "password": "password123", "bio": "Eve the explorer", "avatar": "", "location": "Exploria"},
    {"username": "frank", "email": "frank@example.com", "password": "password123", "bio": "Frank's world", "avatar": "", "location": "Frankfurt"},
]

class Command(BaseCommand):
    help = 'Seed the database with initial users and profiles.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        for user_data in USER_DATA:
            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults={
                    "email": user_data["email"],
                }
            )
            if created:
                user.set_password(user_data["password"])
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user: {user.username}"))
            else:
                self.stdout.write(f"User already exists: {user.username}")
            # Profile
            Profile.objects.update_or_create(
                user=user,
                defaults={
                    "bio": user_data["bio"],
                    "avatar": user_data["avatar"],
                    "location": user_data["location"]
                }
            )
        self.stdout.write(self.style.SUCCESS("User and profile seeding complete."))
