(function($) {
    'use strict';

    $(document).ready(function() {
        const $examSelect = $('#id_exam');
        const $sectionSelect = $('#id_section');

        if ($examSelect.length && $sectionSelect.length) {
            $examSelect.on('change', function() {
                const examId = $(this).val();
                if (examId) {
                    $.ajax({
                        url: `/admin/multilevel/section/?exam=${examId}`,
                        method: 'GET',
                        dataType: 'json',
                        success: function(data) {
                            $sectionSelect.empty().append('<option value="" selected>Bo\'limni tanlang</option>');
                            $.each(data, function(index, section) {
                                $sectionSelect.append($('<option>', {
                                    value: section.id,
                                    text: section.title
                                }));
                            });
                            // Select2 ni qayta ishga tushirish
                            if ($.fn.select2) {
                                $sectionSelect.select2({ width: '100%' });
                            }
                            // Jazzminning tab o‘zgarishi bilan sinxronlash
                            window.dispatchEvent(new Event('resize'));
                        },
                        error: function(xhr) {
                            $sectionSelect.empty().append('<option value="" selected>Xatolik yuz berdi</option>');
                            console.error('AJAX error:', xhr.responseText);
                        }
                    });
                } else {
                    $sectionSelect.empty().append('<option value="" selected>Bo\'limni tanlang</option>');
                }
            });

            // Dastlabki qiymatni yuklash
            if ($examSelect.val()) {
                $examSelect.trigger('change');
            }

            // Select2 ni qo‘llash
            if ($.fn.select2) {
                $examSelect.select2({ width: '100%' });
                $sectionSelect.select2({ width: '100%' });
            }
        }

        // Jazzminning `change_form.js` bilan integratsiya
        window.dispatchEvent(new Event('resize'));
    });

    // Yangi inline qator qo'shilganda Select2 ni qo‘llash
    django.jQuery(document).on('formset:added', function() {
        if ($.fn.select2) {
            $('.select2').select2({ width: '100%' });
        }
    });
})(django.jQuery);