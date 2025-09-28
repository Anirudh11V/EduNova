from rest_framework import serializers

from courses.models import Category, Course, Module, Lesson, Review
from enrollment.models import Enroll
from discussion.models import Post


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'Name', 'slug']


class CourseListSerializer(serializers.ModelSerializer):
    # Custom field to get instructor username
    instructor = serializers.CharField(source = 'instructor.username', read_only= True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'thumbnail', 'instructor']


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'content_type', 'order']


class ModuleSerializer(serializers.ModelSerializer):
    # This nests the LessonSerializer, showing all lesson for this module.
    # The source 'lesson' comes from the related_name on the module foreignkey in the lesson model.

    lessons = LessonSerializer(many= True, read_only= True, source= 'lesson')

    class Meta:
        model = Module
        fields = ['id', 'title', 'slug', 'lessons', 'order']


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor = serializers.CharField(source= 'instructor.username', read_only= True)

    # This nests the ModuleSerializer, showing all modules for this course.
    modules = ModuleSerializer(many= True, read_only= True)

    # This nests the CategorySerialier to show category details.
    category = CategorySerializer(read_only= True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'description', 'thumbnail', 'instructor', 'category', 'modules']


class EnrolledCourseSerializer(serializers.ModelSerializer):
    # Nest he CourseDetailSerializer to show the course details.
    course = CourseDetailSerializer(read_only= True)

    # Include progress percentage property from the model.
    progress_percentage = serializers.ReadOnlyField()

    class Meta:
        model = Enroll
        fields = ['course', 'progress_percentage']


class ReviewSerializer(serializers.ModelSerializer):
    # Make the student field read only because we'll set it automatically in the view.
    student = serializers.CharField(source= 'student.username', read_only= True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'student', 'created_at']
        read_only_fields = ['student', 'created_at']

    def validate(self, data):
        """ Check that a student has not already reviewed this course. """
        # This course object is passed from the view to the serialiers context.
        course = self.context['course']
        student = self.context['request'].user

        if Review.objects.filter(course= course, student= student).exists():
            raise serializers.ValidationError("You have already reviewed this course.")
        return data
    

class ModuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['title']


class ReplySerializer(serializers.ModelSerializer):
    """ A serilaizer for nested replies. """
    author = serializers.CharField(source= 'author.username', read_only= True)

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    """ A serializer for top level posts (topics) that includes nested replies. """
    author = serializers.CharField(source= 'author.username', read_only= True)

    # The replies here comes for the related_name on the parent field.
    replies = ReplySerializer(many= True, read_only= True)

    class Meta:
        model = Post
        fields = ['id', 'author', 'title', 'content', 'created_at', 'replies']
        read_only_fields = ['author', 'created_at', 'replies']


class PostCreateSerializer(serializers.ModelSerializer):
    """ A simple serializer for create/update posts and replies. """
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'parent']


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['title', 'description', 'category']