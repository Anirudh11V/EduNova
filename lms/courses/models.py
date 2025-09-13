from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import os

from django.contrib.auth import get_user_model
# Create your models here.

class Category(models.Model):
    Name = models.CharField(max_length= 50, unique= True)
    slug = models.SlugField(max_length= 50, unique= True, blank= True)
    description = models.TextField(blank= True, null= True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug= slugify(self.Name)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.Name
    
    def get_absolute_url(self):
        return reverse('courses:course_list', args=[self.slug])
    

def course_thumbnail_path(instance, filename):
    """ Generates a unique path for course thumbnails. """
    ext = filename.split('.')[-1]

    # Generates a unique filename using uuid to prevent overwrites
    filename = f'{uuid.uuid4()}.{ext}'

    # Return the new path in the format: courses/<course_slug>/<unique_filename>
    return os.path.join('courses', instance.slug, filename)

class Course(models.Model):
    title = models.CharField(max_length= 50)
    slug = models.SlugField(max_length= 50, unique= True, blank= True)
    description = models.TextField()

    category = models.ForeignKey(Category, on_delete= models.SET_NULL, null= True, related_name= "courses")

    instructor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.SET_NULL,
                                   null= True, limit_choices_to= {'is_instructor': True},
                                   related_name= 'taught_courses')   
    
    price = models.DecimalField(max_digits= 7, decimal_places= 2, default= 0.00)
    thumbnail = models.ImageField(blank= True, null= True, upload_to= course_thumbnail_path)
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateField(auto_now= True)
    is_published = models.BooleanField(default= False)

    class Meta:
        ordering= ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug= slugify(self.title)
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('courses:course_details', args= [self.slug])
    
    @property
    def average_rating(self):
        avg = self.reviews.all().aggregate(Avg('rating'))['rating__avg']
        if avg is None:
            return 0
        return round(avg, 1)
    

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete= models.CASCADE, related_name= 'modules')

    slug = models.SlugField(max_length= 50, blank= True)
    title = models.CharField(max_length= 50)
    description = models.TextField(blank= True, null= True)
    order = models.PositiveIntegerField(default= 1, blank= False, null= False)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug= slugify(self.title)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order}, {self.title} ({self.course.title})" 

    def get_absolute_url(self):
        return reverse('courses:course_details', args= [self.course.slug])   


def lesson_content_path(instance, filename):
    """ Generates a unique path for lesson videos and attachements. """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'

    # Return path: courses/<course_slug>/<module_slug>/<lesson_slug>/<filename>
    return os.path.join(
        'courses',
        instance.module.course.slug,
        instance.module.slug,
        instance.slug,
        filename
    )


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete= models.CASCADE, related_name= 'lesson')

    title = models.CharField(max_length= 50)
    slug = models.SlugField(max_length= 50, blank= True)

    CONTENT_CHOICES = (
        ('text', 'Text content'), 
        ('videourl','Video URL'),
        ('video', 'Video content'),
        ('file', 'File content'),
    )
    content_type = models.CharField(max_length= 50,
                                    choices= CONTENT_CHOICES, default= 'text')
    
    text_content = models.TextField(blank= True, null= True)
    video_url = models.URLField(max_length= 250, blank= True, null= True)
    video = models.FileField(upload_to= lesson_content_path, blank= True, null= True)
    file_upload = models.FileField(blank=True, null= True, upload_to= lesson_content_path)
    order = models.PositiveIntegerField(blank= False, null= False, default= 1)
    created_at = models.DateTimeField(auto_now_add= True)
    updated_at = models.DateField(auto_now= True)
    is_published = models.BooleanField(default= False)

    class Meta:
        ordering = ['order']
        unique_together = ('module', 'order')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.order}, {self.title} ({self.module.title})"
    
    def get_absolute_url(self):
        return reverse('courses:lesson_details', args=[self.module.course.slug, self.module.slug, self.slug])
    

User = get_user_model()

class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete= models.CASCADE, related_name= 'comments')
    author = models.ForeignKey(User, on_delete= models.CASCADE, related_name= 'comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add= True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comments by {self.author.username} on {self.lesson.title}."
    

class Review(models.Model):
    course = models.ForeignKey(Course, on_delete= models.CASCADE, related_name= 'reviews')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name= 'reviews',
                                limit_choices_to= {'is_student': True})
    
    rating = models.PositiveIntegerField(
        validators= [MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank= True, null= True)
    created_at = models.DateTimeField(auto_now_add= True)

    class Meta:
        unique_together= ('course', 'student')
        ordering = ['-created_at']

    def __str__(self):
        return f"Review for {self.course.title} by {self.student.username}."