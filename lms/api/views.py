from django.shortcuts import get_object_or_404
from django.db.models import Max

from rest_framework import generics, filters, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from courses.models import Course, Category, Review, Module
from enrollment.models import Enroll
from discussion.models import Post
from .serializers import (CategorySerializer, CourseListSerializer, CourseDetailSerializer, ModuleSerializer,
                          EnrolledCourseSerializer, ReviewSerializer, PostSerializer, PostCreateSerializer, 
                          ReplySerializer, CourseCreateUpdateSerializer)
from .permissions import IsInstructorAndOwner, IsEnrolledOrAuthor, IsEnrolledOrPostAuthor, IsCourseInstructorOrAdmin

# Create your views here.

class CategoryListAPIView(generics.ListAPIView):
    """ Api view to list all categories. """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CourseViewSet(viewsets.ModelViewSet):
    """ A simple viewset for viewing published courses. """
    queryset = Course.objects.all()
    lookup_field = 'slug'
    permission_classes = [IsCourseInstructorOrAdmin]

    filterset_fields = ['category__slug']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']

    # Because we added new backends, we need to specify which ones this view users.
    # Note: DjangoFilterBackends is already set as a default in settings.py.
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]

    def get_queryset(self):
        # Only show published course in lists, but allow instructor to see their draft.
        if self.action == 'list' and not self.request.user.is_staff:
            return Course.objects.filter(is_published= True)
        return Course.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        elif self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer
    
    def perform_create(self, serializer):
        # Automatically assign the current user as the instructor
        serializer.save(instructor= self.request.user)


class MyCoursesAPIView(generics.ListAPIView):
    """ Api view to list courses the current user is enrolled in. """
    serializer_class = EnrolledCourseSerializer

    # This ensures only authenticated user can access the view.
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter the enrollments based on the currrently logged in user.
        return Enroll.objects.filter(student= self.request.user)
    

class ModuleViewSet(viewsets.ModelViewSet):
    """ A viewset for viewing, creating, updating, deleting module. """

    serializer_class = ModuleSerializer
    # Apply permissions: user must be logged in, and for object-level actions, must be the owner.
    permission_classes = [IsAuthenticated, IsInstructorAndOwner]

    def queryset(self):
        # Filter modules to only belonging to the course in the url.
        return Module.objects.filter(course__slug= self.kwargs['course_slug'])
    
    def perform_create(self, serialier):
        course = get_object_or_404(Course, slug= self.kwargs['course_slug'])

        # check permission before creating.
        if not self.request.user.is_instructor or course.instructor != self.request.user:
            raise PermissionDenied("You do not have permission to add modules to this course.")
        
        max_order = course.modules.aggregrate(Max('order'))['order__max']
        new_order = (max_order or 0) + 1

        serialier.save(course= course, order= new_order)


class ReviewViewSet(viewsets.ModelViewSet):
    """ A viewset for listing, creating, updating, deleting reviews. """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsEnrolledOrAuthor]
    throttle_classes = 'post'

    def get_queryset(self):
        # Filter reviews to only those belonging to the course in the url
        return Review.objects.filter(course__slug= self.kwargs['course_slug'])
    
    def get_serializer_context(self):
        # Pass course and request to the serializer for validation
        context = super().get_serializer_context()
        context['course'] = get_object_or_404(Course, slug= self.kwargs['course_slug'])
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        course =get_object_or_404(Course, slug= self.kwargs['course_slug'])
        # The IsEnrolledOrAuthor permission already checks if the user is enrolled.
        serializer.save(student= self.request.user, course= course)


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsEnrolledOrPostAuthor]
    throttle_classes = 'post'

    def get_queryset(self):
        #  This queryset lists only top level posts (replies).
        return Post.objects.filter(course__slug= self.kwargs['course_slug'], parent__isnull= True)
    
    def serializer_class(self):
        # Use differnet serializer for create/update vs viewing.
        if self.action in ['create', 'update', 'partial_update']:
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        course = get_object_or_404(Course, slug= self.kwargs['course_slug'])
        serializer.save(author= self.request.user, course= course)