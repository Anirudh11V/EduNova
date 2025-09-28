from django.shortcuts import get_object_or_404

from rest_framework import permissions
from enrollment.models import Enroll
from courses.models import Course
from discussion.models import Post


class IsInstructorAndOwner(permissions.BasePermission):
    """ Custom permission to only allow owners of a course to edit it or its childern. SuperUsers are always allowed. """

    def has_object_permission(self, request, view, obj):
        # SuperUser.
        if request.user.is_superuser:
            return True
        
        # This permission is for object-level checks (update, delate).
        # We check if the user is the instructor of the course the modyle belongs to.
        return obj.course.instructor == request.user
    

class IsEnrolledOrAuthor(permissions.BasePermission):
    """ Allows creation for enrolled students. Allows update/delete only for the author of the review. """
    def has_permission(self, request, view):
        # This check is for list and create actions.
        if view.action == 'create':
            course = Course.objects.get(slug= view.kwargs['course_slug'])
            return Enroll.objects.filter(student= request.user, course= course).exists()
        return True
    
    def has_object_permission(self, request, view, obj):
        # This check is for detail actions retrieve, update, delete.
        # Allow read only permission for any request.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permission are only allowed to the author of the review
        return obj.student == request.user
    

class IsEnrolledOrPostAuthor(permissions.BasePermission):
    """ Allows creation for enrolled students in a course's discussion.
        Allows update/delete only for the author of the post.
        SuperUsers are always allowed. """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if not request.user.is_authenticated:
            return False
        course = get_object_or_404(Course, slug= view.kwargs['course_slug'])
        return Enroll.objects.filter(student= request.user, course= course).exists()
    
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return obj.author == request.user
    

class IsCourseInstructorOrAdmin(permissions.BasePermission):
    """ Allows full access to admins.
        Allows instructors to create and update and delete their own courses ONLY if it has no students. """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Allow anyone to list courses, but an instructor to create.
        if view.action == 'create':
            return request.user.is_instructor
        return True
    
    def has_object_permission(self, request, obj, view):
        # Admins can do anything.
        if request.user.is_superuser:
            return True
        
        # Check if the user is the instructor of this course.
        is_owner = obj.instructor == request.user

        # If trying to delete, check for enrollments.
        if view.sction == 'delete':
            return is_owner and obj.enroll_set.count() == 0
        return is_owner