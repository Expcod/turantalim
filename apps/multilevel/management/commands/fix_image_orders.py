from django.core.management.base import BaseCommand
from apps.multilevel.models import TestImage, QuestionImage


class Command(BaseCommand):
    help = 'Fix image orders for existing TestImage and QuestionImage objects'

    def handle(self, *args, **options):
        self.stdout.write('Starting to fix image orders...')
        
        # Fix TestImage orders
        test_images_fixed = 0
        test_groups = {}
        
        # Group TestImages by test
        for test_image in TestImage.objects.all():
            test_id = test_image.test_id
            if test_id not in test_groups:
                test_groups[test_id] = []
            test_groups[test_id].append(test_image)
        
        # Fix orders for each test group
        for test_id, images in test_groups.items():
            # Sort by created_at to maintain chronological order
            images.sort(key=lambda x: x.created_at)
            
            for index, image in enumerate(images, 1):
                if image.order != index:
                    old_order = image.order
                    image.order = index
                    image.save()
                    test_images_fixed += 1
                    self.stdout.write(
                        f'Fixed TestImage {image.id}: order {old_order} -> {index}'
                    )
        
        # Fix QuestionImage orders
        question_images_fixed = 0
        question_groups = {}
        
        # Group QuestionImages by question
        for question_image in QuestionImage.objects.all():
            question_id = question_image.question_id
            if question_id not in question_groups:
                question_groups[question_id] = []
            question_groups[question_id].append(question_image)
        
        # Fix orders for each question group
        for question_id, images in question_groups.items():
            # Sort by created_at to maintain chronological order
            images.sort(key=lambda x: x.created_at)
            
            for index, image in enumerate(images, 1):
                if image.order != index:
                    old_order = image.order
                    image.order = index
                    image.save()
                    question_images_fixed += 1
                    self.stdout.write(
                        f'Fixed QuestionImage {image.id}: order {old_order} -> {index}'
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {test_images_fixed} TestImage orders and {question_images_fixed} QuestionImage orders!'
            )
        )
