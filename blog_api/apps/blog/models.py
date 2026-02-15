from django.db.models import Model, CharField, SlugField, CASCADE, SET_NULL, DateTimeField, ForeignKey, TextField, ManyToManyField, TextChoices
from apps.users.models import CustomUser

class Category(Model):
    name = CharField(max_length=180)
    slug = SlugField(unique=True)

    def __str__(self):
        return self.name

class Tag(Model):
    name = CharField(max_length=50)
    slug = SlugField(unique=True)

    def __str__(self):
        return self.name

class Post(Model):
    class Status(TextChoices):
        DRAFT = 'DR', 'Draft'
        PUBLISHED = 'PB', 'Published'

    author = ForeignKey(CustomUser, on_delete=CASCADE)
    title = CharField(max_length=200)
    slug = SlugField(unique=True)
    body = TextField()
    category = ForeignKey(Category, on_delete=SET_NULL, null=True, related_name='posts')
    tags = ManyToManyField(Tag, blank=True)
    
    # Correct usage of choices
    status = CharField(
        max_length=2,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Comment(Model):
    post = ForeignKey(Post, on_delete=CASCADE, related_name='comments')
    author = ForeignKey(CustomUser, on_delete=CASCADE)
    body = TextField()
    created_at = DateTimeField(auto_now_add=True)