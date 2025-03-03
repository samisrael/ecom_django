from io import BytesIO
from PIL import Image
from django.core.files import File
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/{self.slug}/'


class Products(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/', blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-date_added',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/{self.category.slug}/{self.slug}/'

    def get_image(self):
        if self.image:
            return 'http://127.0.0.1:8000' + self.image.url
        return ''

    def get_thumbnail(self):
        if self.thumbnail:
            return 'http://127.0.0.1:8000' + self.thumbnail.url

        if self.image:
            self.thumbnail = self.make_thumbnail(self.image)
            self.save(update_fields=['thumbnail'])
            return 'http://127.0.0.1:8000' + self.thumbnail.url

        return ''

    def make_thumbnail(self, image, size=(300, 300)):
        """Creates a uniformly sized thumbnail with cropping."""
        img = Image.open(image)
        img = img.convert('RGB')

        # Crop the image to maintain exact size
        img = self.crop_center(img, size)

        thumb_io = BytesIO()
        img.save(thumb_io, 'JPEG', quality=85)

        return File(thumb_io, name=image.name)

    def save(self, *args, **kwargs):
        """Resize and crop the main image before saving."""
        if self.image:
            self.image = self.resize_and_crop_image(self.image, size=(500, 500))  # Ensure uniform size

        super().save(*args, **kwargs)  # Save resized image

        # Generate thumbnail if not already set
        if self.image and not self.thumbnail:
            self.thumbnail = self.make_thumbnail(self.image)
            super().save(update_fields=['thumbnail'])

    def resize_and_crop_image(self, image_field, size=(500, 500)):
        """Resizes and crops the image to a fixed size."""
        img = Image.open(image_field)
        img = img.convert('RGB')

        # Crop the image to ensure a uniform size
        img = self.crop_center(img, size)

        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=90)

        return File(img_io, name=image_field.name)

    def crop_center(self, img, size):
        """Crops the center of the image to match the target size."""
        img.thumbnail((max(size), max(size)), Image.Resampling.LANCZOS)  # Updated from Image.ANTIALIAS

        width, height = img.size
        target_width, target_height = size

        left = (width - target_width) / 2
        top = (height - target_height) / 2
        right = (width + target_width) / 2
        bottom = (height + target_height) / 2

        return img.crop((left, top, right, bottom))
