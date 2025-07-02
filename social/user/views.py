from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Post, Comment, Like, Follow, UserProfile
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, email=email, password=password1)
        login(request, user)
        messages.success(request, "Registration successful. You are now logged in.")
        return redirect('all_posts')
    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('all_posts')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def follow_user(request, user_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to follow users.")
        return redirect('login')
    to_follow = get_object_or_404(User, id=user_id)
    if to_follow == request.user:
        messages.error(request, "You cannot follow yourself.")
        return redirect('all_posts')
    Follow.objects.get_or_create(follower=request.user, following=to_follow)
    messages.success(request, f"You are now following {to_follow.username}.")
    return redirect('all_posts')

def unfollow_user(request, user_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to unfollow users.")
        return redirect('login')
    to_unfollow = get_object_or_404(User, id=user_id)
    Follow.objects.filter(follower=request.user, following=to_unfollow).delete()
    messages.success(request, f"You have unfollowed {to_unfollow.username}.")
    return redirect('all_posts')

def like_post(request, post_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to like a post.")
        return redirect('login')
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        # If already liked, unlike it
        like.delete()
        messages.info(request, "You unliked the post.")
    else:
        messages.success(request, "You liked the post.")
    return redirect(request.META.get('HTTP_REFERER', 'all_posts'))

def comment_post(request, post_id):
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to comment.")
        return redirect('login')
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Comment.objects.create(user=request.user, post=post, text=text)
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Comment cannot be empty.")
    return redirect(request.META.get('HTTP_REFERER', 'all_posts'))

def search_users(request):
    query = request.GET.get('q', '')
    users = []
    selected_user = None
    user_posts = []
    is_following = False
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)
    user_id = request.GET.get('user_id')
    if user_id:
        selected_user = get_object_or_404(User, id=user_id)
        user_posts = Post.objects.filter(user=selected_user).order_by('-created_at')
        if request.user.is_authenticated and request.user != selected_user:
            is_following = Follow.objects.filter(follower=request.user, following=selected_user).exists()
    context = {
        'users': users,
        'query': query,
        'selected_user': selected_user,
        'user_posts': user_posts,
        'is_following': is_following,
    }
    return render(request, 'user/search.html', context)

def create_post(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to create a post.")
            return redirect('login')
        image = request.FILES.get('image')
        caption = request.POST.get('caption', '')
        if image:
            Post.objects.create(user=request.user, image=image, caption=caption)
            messages.success(request, "Post uploaded successfully!")
            return redirect('all_posts')
        else:
            messages.error(request, "Please select an image to upload.")
    return render(request, 'create_post.html')

def all_posts(request):
    if request.user.is_authenticated:
        posts = Post.objects.filter(user=request.user).order_by('-created_at')
    else:
        posts = Post.objects.none()
    return render(request, 'all_posts.html', {'posts': posts})

def home(request):
    if request.user.is_authenticated:
        # Only users the current user follows (not self)
        following_ids = set(request.user.following.values_list('following_id', flat=True))
        posts = Post.objects.filter(user_id__in=following_ids).order_by('-created_at')
    else:
        posts = Post.objects.none()
        following_ids = set()
    return render(request, 'home.html', {'posts': posts, 'following_ids': following_ids})

def profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    post_count = posts.count()
    follower_count = profile_user.followers.count()
    following_count = profile_user.following.count()
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(follower=request.user, following=profile_user).exists()
    context = {
        'profile_user': profile_user,
        'posts': posts,
        'post_count': post_count,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following,
    }
    return render(request, 'user/profile.html', context)

@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        city_or_village = request.POST.get('city_or_village')
        address = request.POST.get('address')
        social_media_link = request.POST.get('social_media_link')
        bio = request.POST.get('bio')
        profile_image = request.FILES.get('profile_image')

        if User.objects.filter(username=username).exclude(id=user.id).exists():
            messages.error(request, "Username already exists.")
        elif User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, "Email already exists.")
        else:
            user.username = username
            user.email = email
            user.save()
            profile.gender = gender
            profile.city_or_village = city_or_village
            profile.address = address
            profile.social_media_link = social_media_link
            profile.bio = bio
            if profile_image:
                profile.profile_image = profile_image
            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile', user_id=user.id)
    return render(request, 'user/edit_profile.html', {'profile': profile})

def followers_list(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    followers = profile_user.followers.select_related('follower')
    return render(request, 'user/followers_list.html', {
        'profile_user': profile_user,
        'followers': followers,
    })

def following_list(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)
    following = profile_user.following.select_related('following')
    return render(request, 'user/following_list.html', {
        'profile_user': profile_user,
        'following': following,
    })
