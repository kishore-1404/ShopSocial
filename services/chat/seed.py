import random
from sqlalchemy.orm import sessionmaker
from models import Base, ChatMessage
from app import engine
from datetime import datetime

Session = sessionmaker(bind=engine)
session = Session()

USERNAMES = ["alice", "bob", "carol", "dave", "eve", "frank"]
ROOMS = ["room1", "room2", "room3"]

MESSAGES = [
    "Hello!",
    "How are you?",
    "Let's meet up.",
    "Check this out!",
    "See you soon.",
    "Great product!",
    "Thanks!",
    "What's up?",
]

def seed_chats():
    for room in ROOMS:
        for _ in range(random.randint(5, 10)):
            msg = ChatMessage(
                room_id=room,
                sender=random.choice(USERNAMES),
                content=random.choice(MESSAGES),
                timestamp=datetime.utcnow()
            )
            session.add(msg)
    session.commit()
    print("Seeded chat messages.")

def main():
    Base.metadata.create_all(bind=engine)
    seed_chats()

if __name__ == "__main__":
    main()
