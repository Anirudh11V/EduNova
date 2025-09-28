from django.urls import path, include
from . import views

from rest_framework_nested import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView, 
    TokenRefreshView,
)
from drf_spectacular.views import (
    SpectacularAPIView, 
    SpectacularRedocView,
    SpectacularSwaggerView,
)

router = routers.SimpleRouter()

router.register(r'courses', views.CourseViewSet, basename= 'courses')

# A nested router for modules within courses
courses_router = routers.NestedSimpleRouter(router, r'courses', lookup= 'course')
courses_router.register(r'modules', views.ModuleViewSet, basename= 'course_modules')

courses_router.register(r'reviews', views.ReviewViewSet, basename= 'course_review')

courses_router.register(r'posts', views.PostViewSet, basename= 'course_posts')


urlpatterns = [
    # Token 
    path('token/', TokenObtainPairView.as_view(), name= 'token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name= 'token_refresh'),

    # API endpoints
    path('categories/', views.CategoryListAPIView.as_view(), name= 'category-list'),
    path('my_courses/', views.MyCoursesAPIView.as_view(), name= 'my-courses'),

    path('', include(router.urls)),
    path('', include(courses_router.urls)),    
    
    # Documentation
    path('schema/', SpectacularAPIView.as_view(), name= 'schema'),

    # UI
    path('schema/swagger_ui/', SpectacularSwaggerView.as_view(url_name= 'schema'), name= 'swagger_ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name= 'schema'), name= 'redoc'),

]