django.jQuery(document).ready(function($) {
    // Cache selectors
    var $examField = $('#id_exam');
    var $testField = $('#id_test');
    var $textField = $('#id_text');
    var $hasOptionsField = $('#id_has_options');
    var $answerField = $('#id_answer');
    var $saveButton = $('.submit-row input[name="_save"]');
    var $mandatoryFields = $('.field-exam, .field-test, .field-text');
    var $optionalFields = $('.field-picture, .field-has_options, .field-answer');
    var $inlineOptions = $('.inline-related');

    // Initially hide test and other fields
    $testField.closest('.form-row').hide();
    $mandatoryFields.hide();
    $optionalFields.hide();
    $inlineOptions.hide();
    $saveButton.prop('disabled', true);

    // Show test field when exam is selected
    $examField.change(function() {
        var examId = $(this).val();
        $testField.closest('.form-row').hide();
        $mandatoryFields.hide();
        $optionalFields.hide();
        $inlineOptions.hide();
        $saveButton.prop('disabled', true);

        if (examId) {
            $.ajax({
                url: '/admin/multilevel/test/?section__exam__id__exact=' + examId,
                success: function(data) {
                    var options = '<option value="">---------</option>';
                    $.each(data, function(i, test) {
                        options += '<option value="' + test.id + '">' + test.title + '</option>';
                    });
                    $testField.html(options);
                    $testField.closest('.form-row').show();
                },
                error: function() {
                    alert('Testlarni yuklashda xato yuz berdi!');
                }
            });
        }
    });

    // Show other fields when test is selected
    $testField.change(function() {
        if ($(this).val()) {
            $mandatoryFields.show();
            $optionalFields.show();
            $inlineOptions.show();
            checkMandatoryFields();
        } else {
            $mandatoryFields.hide();
            $optionalFields.hide();
            $inlineOptions.hide();
            $saveButton.prop('disabled', true);
        }
    });

    // Show/hide answer and options based on has_options
    $hasOptionsField.change(function() {
        if ($(this).is(':checked')) {
            $answerField.closest('.form-row').hide();
            $inlineOptions.show();
        } else {
            $answerField.closest('.form-row').show();
            $inlineOptions.hide();
        }
    });

    // Enable save button only when mandatory fields are filled
    function checkMandatoryFields() {
        var allFilled = $examField.val() && $testField.val() && $textField.val();
        $saveButton.prop('disabled', !allFilled);
    }

    $examField.change(checkMandatoryFields);
    $testField.change(checkMandatoryFields);
    $textField.on('input', checkMandatoryFields);
});