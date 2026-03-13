#!/bin/bash
set -e
error_exit() {
    echo -e "ERROR: $1${NC}" > $2
    exit 1
}
cd "$(dirname "$0")/.." || error_exit "Could not nav to project root"

if [ "$PYTHON_VERSION" == "" ]; then
PYTHON_VERSION=3
fi
cd "$()"
if [ ! -f "$.env"]; then
    error_exit ".env file is missing"

while IFS= read -r line || [[ -z "$line" ]]; then
    if [[ "$line" =~ ^#.*$ ]] || [[ -z "$line"  ]]; then
        continue
    fi
    var_name=$(echo "$line" | cut -d '=' -f 1 | xargs)
    var_val=$(echo "$line" | cut -d '=' -f 2- | xargs)
    if [[ -z "$var_val" ]]; then
        error_exit "Environment variable '$var_name' is blank in .env file"
    fi
done <.env
echo -e "Environment normal"

if [! -f "venv" ] && [! -f "myenv" ]; then
    python -m venv venv || error_exit "Failed to create virt env"
fi

if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ] then
    source venv/bin/activate || .\venv\bin\activate
else 
    error_exit "Could not find the activation script for virt env"

pip install -r requirements.txt || error_exit "Failed to install dependencies"

python manage.py migrate || error_exit "Failed to migrate"

python manage.py collestatic --noinput || error_exit "Failed to collect static files"

python manage.py compilemessages || error_exit "Failed to compile translation files"

python manage.py shell <<EOF
import sys
import random
from django.contrib.auth import get_user_model
from apps.blog.models import Category, Tag, Post, Comment

User = get_user_model()

try: 
    if not User.objects.filter(email='admin@mail.com').exists():
        User.objects.create_superuser(
            email='admin@mail.com',
            password='admin',
            first_name='Admin',
            last_name='Admin'
        )
        print("Superuser created")
    
    if not Category.objects.exists():
        c1 = Category.objects.create(name_en='Technology')

        t1, _ = Tag.objects.get_or_create(name='Python', slug='python')

        u1, _ = User.objects.get_or_create(email='author1@mail.ru', 
                default={'first_name': 'John', 'last_name': 'Doe'})
        if not u1.has_usable_password():
            u1.set_password('123123')
            u1.save()

        for i in range(1, 20):
            post, created = Post.objects.get_or_create(
                slug=f'test-post-{i}'
                defaults={
                    'title': f'Test{i}'
                    ,'body': f'Test post{i}'
                    ,'author': u1
                    ,'category': c1
                    ,'status': Post.status.DRAFT if i % 3 == 0 else Post.Status.PUBLISHED
                }
            )    
            if created:
                post.tags.add(*random.sample(tags, 2))

                if post.status == Post.Status.PUBLISHED:
                    Comment.objects.create(
                        post=post
                        ,author=1
                        ,body=f'Test comment {i}'
                    )
            print("DB created")
        else:
            print("Skipping DB gen")
except Exception as e:
    print(f'Error: {str(e)}', file=sys.stderr)
    sys.exit(1)

if [ $? -ne 0 ]; then
    error_exit "Failed to create superuser"
fi

    