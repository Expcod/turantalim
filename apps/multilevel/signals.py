"""
Signals for automatic reviewer setup and exam score calculation
"""
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=User.groups.through)
def auto_setup_reviewer(sender, instance, action, pk_set, **kwargs):
    """
    Automatically configure user when added to Reviewer group
    
    When a user is added to the "Reviewer" group:
    - Ensures user is active
    - Does NOT change is_staff or is_superuser (allows admin reviewers)
    
    This makes the user automatically visible in the Tekshiruvchilar (Reviewers) section
    """
    if action == "post_add" and pk_set:
        try:
            # Check if Reviewer group is among the added groups
            reviewer_group = Group.objects.get(name='Reviewer')
            
            if reviewer_group.id in pk_set:
                # User was just added to Reviewer group
                # Only ensure user is active
                if not instance.is_active:
                    instance.is_active = True
                    instance.save(update_fields=['is_active'])
                    
        except Group.DoesNotExist:
            # Reviewer group doesn't exist yet
            pass


@receiver(m2m_changed, sender=User.groups.through)
def cleanup_reviewer_on_remove(sender, instance, action, pk_set, **kwargs):
    """
    Optional: Handle when user is removed from Reviewer group
    
    This doesn't change any permissions, just logs the action for tracking
    """
    if action == "post_remove" and pk_set:
        try:
            reviewer_group = Group.objects.get(name='Reviewer')
            
            if reviewer_group.id in pk_set:
                # User was removed from Reviewer group
                # They will automatically disappear from Tekshiruvchilar section
                pass
                
        except Group.DoesNotExist:
            pass


@receiver(pre_save, sender='multilevel.ManualReview')
def delete_telegram_notification_on_reviewing(sender, instance, **kwargs):
    """
    Delete Telegram notification when submission status changes to 'reviewing'
    
    This prevents other reviewers from seeing and claiming already-being-reviewed submissions
    """
    if not instance.pk:
        # New instance, no need to check for status change
        return
    
    try:
        # Get the old instance from database
        old_instance = sender.objects.get(pk=instance.pk)
        
        # Check if status changed from 'pending' to 'reviewing'
        if old_instance.status == 'pending' and instance.status == 'reviewing':
            # Delete the Telegram notification
            from .telegram_notifications import telegram_notifier
            telegram_notifier.delete_submission_notification(instance)
            logger.info(f"Telegram notification deleted for submission {instance.test_result.id}")
            
    except sender.DoesNotExist:
        # Instance doesn't exist in database yet
        pass
    except Exception as e:
        # Log error but don't break the save process
        logger.error(f"Error deleting Telegram notification: {str(e)}")


@receiver(post_save, sender='multilevel.ManualReview')
def update_exam_score_on_manual_review_completion(sender, instance, created, **kwargs):
    """
    Automatically update final exam score when manual review is completed.
    
    This signal triggers when a ManualReview is saved with status='checked',
    which means the writing or speaking section has been fully reviewed.
    It then checks if all sections are completed and updates the final exam score.
    """
    # Only process when manual review is completed (not created, not draft)
    if not created and instance.status == 'checked' and instance.total_score is not None:
        try:
            from .multilevel_score import update_final_exam_score
            from .models import UserTest
            
            user_test = instance.test_result.user_test
            
            # Only for multilevel and TYS exams
            if user_test.exam.level in ['multilevel', 'tys']:
                # Use transaction to ensure atomicity
                with transaction.atomic():
                    # Update final exam score
                    result = update_final_exam_score(user_test.id)
                    
                    if result['success']:
                        # Refresh user_test from database
                        user_test.refresh_from_db()
                        
                        # Check if all sections are graded
                        if user_test.are_all_sections_graded() and not user_test.is_checked:
                            # Mark as checked
                            user_test.is_checked = True
                            user_test.save(update_fields=['is_checked'])
                            
                            # Send SMS notification ONLY ONCE when is_checked becomes True
                            try:
                                from .utils import send_exam_result_notification
                                send_exam_result_notification(user_test)
                                logger.info(f"SMS yuborildi: UserTest {user_test.id} - Barcha sectionlar baholandi")
                            except Exception as sms_error:
                                logger.error(f"SMS yuborishda xatolik: {str(sms_error)}")
                        
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the save process
            logger.error(f"Error updating final exam score: {str(e)}")


@receiver(post_save, sender='multilevel.TestResult')
def update_exam_score_on_section_completion(sender, instance, created, **kwargs):
    """
    Automatically update final exam score when a section is completed.
    
    This signal triggers when a TestResult is saved with status='completed'.
    It checks if all sections are completed and updates the final exam score.
    
    Note: SMS is NOT sent here. SMS is only sent when ALL sections are graded
    (including manual reviews for writing/speaking), which is handled by the
    ManualReview signal.
    """
    # Only process when test result is completed
    if not created and instance.status == 'completed':
        try:
            from .multilevel_score import update_final_exam_score
            from .models import UserTest
            
            user_test = instance.user_test
            
            # Only for multilevel and TYS exams
            if user_test.exam.level in ['multilevel', 'tys']:
                # Use transaction to ensure atomicity
                with transaction.atomic():
                    # Update final exam score (for sections that don't need manual review)
                    result = update_final_exam_score(user_test.id)
                    
                    if result['success']:
                        # Refresh user_test from database
                        user_test.refresh_from_db()
                        
                        # Check if all sections are graded (in case no manual reviews needed)
                        if user_test.are_all_sections_graded() and not user_test.is_checked:
                            # Mark as checked
                            user_test.is_checked = True
                            user_test.save(update_fields=['is_checked'])
                            
                            # Send SMS notification ONLY ONCE when is_checked becomes True
                            try:
                                from .utils import send_exam_result_notification
                                send_exam_result_notification(user_test)
                                logger.info(f"SMS yuborildi: UserTest {user_test.id} - Barcha sectionlar baholandi")
                            except Exception as sms_error:
                                logger.error(f"SMS yuborishda xatolik: {str(sms_error)}")
                        
        except Exception as e:
            # Log the error but don't raise it to avoid breaking the save process
            logger.error(f"Error updating final exam score: {str(e)}")

