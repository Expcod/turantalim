# Migration to fix CASCADE behavior for all related models

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('multilevel', '0031_fix_manualreview_cascade'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Fix SubmissionMedia cascade
                ALTER TABLE multilevel_submissionmedia 
                DROP CONSTRAINT IF EXISTS multilevel_submissio_test_result_id_77de410c_fk_multileve;
                
                ALTER TABLE multilevel_submissionmedia 
                ADD CONSTRAINT multilevel_submissio_test_result_id_77de410c_fk_multileve
                FOREIGN KEY (test_result_id) 
                REFERENCES multilevel_testresult(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
                
                -- Fix QuestionScore cascade
                ALTER TABLE multilevel_questionscore 
                DROP CONSTRAINT IF EXISTS multilevel_questionscore_manual_review_id_a9c4e673_fk;
                
                ALTER TABLE multilevel_questionscore 
                ADD CONSTRAINT multilevel_questionscore_manual_review_id_a9c4e673_fk
                FOREIGN KEY (manual_review_id) 
                REFERENCES multilevel_manualreview(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
                
                -- Fix ReviewLog cascade
                ALTER TABLE multilevel_reviewlog 
                DROP CONSTRAINT IF EXISTS multilevel_reviewlog_manual_review_id_80b8d510_fk;
                
                ALTER TABLE multilevel_reviewlog 
                ADD CONSTRAINT multilevel_reviewlog_manual_review_id_80b8d510_fk
                FOREIGN KEY (manual_review_id) 
                REFERENCES multilevel_manualreview(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
                
                -- Fix UserAnswer cascade
                ALTER TABLE multilevel_useranswer 
                DROP CONSTRAINT IF EXISTS multilevel_useranswe_test_result_id_c494d18e_fk_multileve;
                
                ALTER TABLE multilevel_useranswer 
                ADD CONSTRAINT multilevel_useranswe_test_result_id_c494d18e_fk_multileve
                FOREIGN KEY (test_result_id) 
                REFERENCES multilevel_testresult(id) 
                ON DELETE CASCADE 
                DEFERRABLE INITIALLY DEFERRED;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

