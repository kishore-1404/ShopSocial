# User Service


This service provides user management and social features for ShopSocial, built with Django and Django REST Framework (DRF).

## Architecture

This service uses a modular architecture with a dedicated service layer:
- **accounts/service.py** contains all business logic and database operations.
- **accounts/views.py** contains only HTTP request/response handling, delegating to the service layer.

This separation improves maintainability, testability, and production readiness.

## Features
- User registration and authentication
- User profiles (bio, avatar, location)
- Follow/unfollow users
- Followers and following lists
- Social feed (posts from followed users)
- Like/unlike posts
- Comment on posts

## API Endpoints

| Method | Endpoint              | Description                  | Auth Required |
|--------|-----------------------|------------------------------|---------------|
| POST   | /register/            | Register a new user          | No            |
| GET/PUT| /profile/             | Get/update user profile      | Yes           |
| POST   | /follow/              | Follow a user                | Yes           |
| POST   | /unfollow/            | Unfollow a user              | Yes           |
| GET    | /followers/           | List your followers          | Yes           |
| GET    | /following/           | List users you follow        | Yes           |
| GET    | /feed/                | Get posts from followed users| Yes           |
| POST   | /like/                | Like a post                  | Yes           |
| POST   | /unlike/              | Unlike a post                | Yes           |
| GET    | /comments/?post_id=   | List comments for a post     | Yes           |
| POST   | /comments/create/     | Add a comment to a post      | Yes           |

## Models
- **User**: Django built-in user
- **Profile**: One-to-one with User, stores bio, avatar, location
- **Post**: User-generated content
- **Like**: User likes on posts
- **Comment**: User comments on posts
- **Follower**: Follower/following relationships

## Setup
1. Install dependencies:
	```sh
	pip install -r requirements.txt
	```
2. Run migrations:
	```sh
	python manage.py migrate
	```
3. Start the server:
	```sh
	python manage.py runserver
	```

## Notes
- All endpoints except registration require authentication (JWT recommended).
- See `accounts/urls.py` for full endpoint list.
- Social features (follow, like, comment) are available only to authenticated users.

---
*This README was auto-generated and includes all useful information from previous documentation.*