(function($) {
    $(document).ready(function() {
        // Exam select field
        var $exam = $('#id_exam');
        var $section = $('#id_section');

        function updateSections(examId, selectedSectionId) {
            if (!examId) {
                $section.html('<option value="">---------</option>');
                return;
            }
            $.ajax({
                url: '/admin/multilevel/test/get_sections_for_exam/',
                data: { exam: examId },
                success: function(data) {
                    $section.html('<option value="">---------</option>');
                    $.each(data.sections, function(i, section) {
                        var selected = (section.id == selectedSectionId) ? 'selected' : '';
                        $section.append('<option value="' + section.id + '" ' + selected + '>' + section.title + '</option>');
                    });
                }
            });
        }

        // On Exam change
        $exam.change(function() {
            updateSections($(this).val(), null);
        });

        // On page load, if Exam is selected, update Section options
        var initialExam = $exam.val();
        var initialSection = $section.val();
        if (initialExam) {
            updateSections(initialExam, initialSection);
        }
    });
})(django.jQuery); 