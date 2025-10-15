# Migration to fix CASCADE behavior for ManualReview.test_result

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('multilevel', '0030_alter_manualreview_id_alter_questionscore_id_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Drop existing foreign key constraint
                ALTER TABLE multilevel_manualreview 
                DROP CONSTRAINT IF EXISTS multilevel_manualrev_test_result_id_18133c6b_fk_multileve;
                
                -- Add new foreign key constraint with CASCADE
                ALTER TABLE multilevel_manualreview 
                ADD CONSTRAINT multilevel_manualrev_test_result_id_18133c6b_fk_multileve 
                FOREIGN KEY (test_result_id) 
                REFERENCES multilevel_testresult(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql="""
                -- Revert to old constraint (without CASCADE)
                ALTER TABLE multilevel_manualreview 
                DROP CONSTRAINT IF EXISTS multilevel_manualrev_test_result_id_18133c6b_fk_multileve;
                
                ALTER TABLE multilevel_manualreview 
                ADD CONSTRAINT multilevel_manualrev_test_result_id_18133c6b_fk_multileve 
                FOREIGN KEY (test_result_id) 
                REFERENCES multilevel_testresult(id) 
                DEFERRABLE INITIALLY DEFERRED;
            """
        ),
    ]

