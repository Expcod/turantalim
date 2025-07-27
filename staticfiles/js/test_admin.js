django.jQuery(document).ready(function($) {
    // Cache selectors
    var $examField = $('#id_exam');
    var $sectionField = $('#id_section');
    var $titleField = $('#id_title');
    var $descriptionField = $('#id_description');
    var $orderField = $('#id_order');
    var $saveButton = $('.submit-row input[name="_save"]');
    var $mandatoryFields = $('.field-exam, .field-section, .field-title, .field-description, .field-order');
    var $optionalFields = $('.field-text_title, .field-text, .field-options_array, .field-sample, .field-constraints');
    var $pictureField = $('.field-picture');
    var $audioField = $('.field-audio');

    // Initially hide section and other fields
    $sectionField.closest('.form-row').hide();
    $mandatoryFields.hide();
    $optionalFields.hide();
    $pictureField.hide();
    $audioField.hide();
    $saveButton.prop('disabled', true);

    // Show section field when exam is selected
    $examField.change(function() {
        var examId = $(this).val();
        $sectionField.closest('.form-row').hide();
        $mandatoryFields.hide();
        $optionalFields.hide();
        $pictureField.hide();
        $audioField.hide();
        $saveButton.prop('disabled', true);

        if (examId) {
            $.ajax({
                url: '/admin/multilevel/section/?exam__id__exact=' + examId,
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    $.each(data, function(i, section) {
                        options += '<option value="' + section.id + '">' + section.title + '</option>';
                    });
                    $sectionField.html(options);
                    $sectionField.closest('.form-row').show();
                },
                error: function() {
                    alert('Bo‘limlarni yuklashda xato yuz berdi!');
                }
            });
        }
    });

    // Show other fields when section is selected
    $sectionField.change(function() {
        if ($(this).val()) {
            $mandatoryFields.show();
            $pictureField.show();
            $audioField.show();
            $optionalFields.closest('.fieldset').find('h2').show(); // Show collapsible section
            checkMandatoryFields();
        } else {
            $mandatoryFields.hide();
            $pictureField.hide();
            $audioField.hide();
            $optionalFields.hide();
            $saveButton.prop('disabled', true);
        }
    });

    // Enable save button only when mandatory fields are filled
    function checkMandatoryFields() {
        var allFilled = $examField.val() && $sectionField.val() && $titleField.val() && $descriptionField.val() && $orderField.val();
        $saveButton.prop('disabled', !allFilled);
    }

    $examField.change(checkMandatoryFields);
    $sectionField.change(checkMandatoryFields);
    $titleField.on('input', checkMandatoryFields);
    $descriptionField.on('input', checkMandatoryFields);
    $orderField.on('input', checkMandatoryFields);
});