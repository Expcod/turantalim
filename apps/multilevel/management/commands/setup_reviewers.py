"""
Management command to set up Reviewer group and permissions
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from apps.multilevel.models import ManualReview, QuestionScore, ReviewLog, SubmissionMedia


class Command(BaseCommand):
    help = 'Setup Reviewer group with appropriate permissions for manual review system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Reviewer group...')
        
        # Create or get the Reviewer group
        reviewer_group, created = Group.objects.get_or_create(name='Reviewer')
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created Reviewer group'))
        else:
            self.stdout.write(self.style.WARNING('→ Reviewer group already exists'))
        
        # Get content types for our models
        manual_review_ct = ContentType.objects.get_for_model(ManualReview)
        question_score_ct = ContentType.objects.get_for_model(QuestionScore)
        review_log_ct = ContentType.objects.get_for_model(ReviewLog)
        submission_media_ct = ContentType.objects.get_for_model(SubmissionMedia)
        
        # Define permissions for reviewers
        # They can view and change manual reviews, but not delete
        permissions_to_add = [
            # ManualReview permissions
            Permission.objects.get(codename='view_manualreview', content_type=manual_review_ct),
            Permission.objects.get(codename='change_manualreview', content_type=manual_review_ct),
            
            # QuestionScore permissions
            Permission.objects.get(codename='view_questionscore', content_type=question_score_ct),
            Permission.objects.get(codename='add_questionscore', content_type=question_score_ct),
            Permission.objects.get(codename='change_questionscore', content_type=question_score_ct),
            
            # ReviewLog permissions (view only)
            Permission.objects.get(codename='view_reviewlog', content_type=review_log_ct),
            
            # SubmissionMedia permissions (view only)
            Permission.objects.get(codename='view_submissionmedia', content_type=submission_media_ct),
        ]
        
        # Add permissions to group
        reviewer_group.permissions.set(permissions_to_add)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Added {len(permissions_to_add)} permissions to Reviewer group'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Setup completed successfully!'))
        self.stdout.write('')
        self.stdout.write('Reviewer permissions:')
        for perm in permissions_to_add:
            self.stdout.write(f'  - {perm.codename}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('To add a user to Reviewer group:'))
        self.stdout.write('  1. Go to Django Admin (/admin/)')
        self.stdout.write('  2. Navigate to Users -> Select user')
        self.stdout.write('  3. In Groups section, add "Reviewer" group')
        self.stdout.write('  4. Save the user')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Note: Reviewers can access admin-dashboard but NOT Django admin panel'))
