"""
Django management command to reset stale manual reviews.

This command finds manual reviews that have been in 'reviewing' status
for more than 12 hours and resets them to 'pending' status so other
reviewers can pick them up.

Usage:
    python manage.py reset_stale_reviews
    
    python manage.py reset_stale_reviews --dry-run  # Preview changes
    python manage.py reset_stale_reviews --hours 6  # Custom hours threshold
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta

from apps.multilevel.models import ManualReview


class Command(BaseCommand):
    help = 'Reset manual reviews that have been in reviewing status for more than 12 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=12,
            help='Hours threshold for considering a review stale (default: 12)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        hours_threshold = options['hours']
        verbose = options['verbose']
        
        # Calculate the cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours_threshold)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Looking for reviews in 'reviewing' status since before {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )
        
        # Find stale reviews
        stale_reviews = ManualReview.objects.filter(
            status='reviewing',
            updated_at__lt=cutoff_time
        ).select_related(
            'test_result__user_test__user',
            'test_result__user_test__exam',
            'reviewer'
        )
        
        total_count = stale_reviews.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No stale reviews found. All reviews are within the time limit.")
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f"Found {total_count} stale reviews to reset:")
        )
        
        # Show details of what will be changed
        for review in stale_reviews:
            user_name = review.test_result.user_test.user.get_full_name()
            exam_title = review.test_result.user_test.exam.title
            reviewer_name = review.reviewer.get_full_name() if review.reviewer else "Unknown"
            time_since_update = timezone.now() - review.updated_at
            
            self.stdout.write(
                f"  - {user_name} ({exam_title}) - "
                f"Reviewer: {reviewer_name} - "
                f"Last updated: {review.updated_at.strftime('%Y-%m-%d %H:%M:%S')} "
                f"({time_since_update.total_seconds() // 3600:.1f} hours ago)"
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDRY RUN: Would reset {total_count} reviews to 'pending' status."
                )
            )
            return
        
        # Ask for confirmation (skip in non-interactive mode)
        import sys
        if sys.stdin.isatty():
            confirm = input(f"\nReset {total_count} reviews to 'pending' status? (y/N): ")
            if confirm.lower() != 'y':
                self.stdout.write("Operation cancelled.")
                return
        else:
            # Non-interactive mode - proceed automatically
            self.stdout.write(f"\nNon-interactive mode: Proceeding with reset of {total_count} reviews.")
        
        # Perform the reset
        reset_count = 0
        with transaction.atomic():
            for review in stale_reviews:
                old_reviewer = review.reviewer.get_full_name() if review.reviewer else "Unknown"
                
                # Reset to pending
                review.status = 'pending'
                review.reviewer = None
                review.total_score = None
                review.reviewed_at = None
                review.save()
                
                reset_count += 1
                
                if verbose:
                    self.stdout.write(
                        f"  ✓ Reset {review.test_result.user_test.user.get_full_name()}'s "
                        f"{review.section} review (was assigned to {old_reviewer})"
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully reset {reset_count} reviews to 'pending' status."
            )
        )
        
        # Show summary
        self.stdout.write(
            self.style.SUCCESS(
                f"These reviews are now available for other reviewers to pick up."
            )
        )
