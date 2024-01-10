from django.utils import timezone

new_user = AppUser(
    access_token='token123', 
    email='user1@example.com', 
    provider='provider1', 
    provider_id='prov1', 
    image='http://example.com/image1.jpg', 
    two_fact=False, 
    nickname='nick1', 
    language='English',
    created_at=timezone.now(),
    updated_at=timezone.now()
)
new_user.save()
