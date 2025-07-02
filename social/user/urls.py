from django.urls import path
from . import views

urlpatterns = [
    # User authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Social features
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('comment/<int:post_id>/', views.comment_post, name='comment_post'),
    path('search/', views.search_users, name='search_users'),
    path('post/', views.create_post, name='create_post'),
    path('all_posts/', views.all_posts, name='all_posts'),
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('profile/<int:user_id>/followers/', views.followers_list, name='followers_list'),
    path('profile/<int:user_id>/following/', views.following_list, name='following_list'),

    # Home page
    path('', views.home, name='home'),
]
