(function($) {
      'use strict';

      $(document).ready(function() {
          var $exam = $('#id_exam');
          var $section = $('#id_section');

          function updateSections(examId, selectedSectionId) {
              if (!examId) {
                  $section.html('<option value="">Bo\'limni tanlang</option>');
                  return;
              }
              $.ajax({
                  url: '/admin/multilevel/test/get_sections_for_exam/',
                  data: { exam: examId },
                  dataType: 'json',
                  success: function(data) {
                      if (data.error) {
                          $section.html('<option value="">Xatolik: ' + data.error + '</option>');
                          console.error(data.error);
                          return;
                      }
                      $section.html('<option value="">Bo\'limni tanlang</option>');
                      $.each(data.sections, function(i, section) {
                          var selected = (section.id == selectedSectionId) ? 'selected' : '';
                          $section.append('<option value="' + section.id + '" ' + selected + '>' + section.title + '</option>');
                      });
                      // Select2 ni qayta ishga tushirish
                      if ($.fn.select2) {
                          $section.select2({ width: '100%' });
                      }
                      // Jazzmin bilan sinxronlash
                      window.dispatchEvent(new Event('resize'));
                  },
                  error: function(xhr, status, error) {
                      $section.html('<option value="">Xatolik yuz berdi</option>');
                      console.error('AJAX error:', error, xhr.responseText);
                  }
              });
          }

          // Exam o‘zgarganda
          $exam.on('change', function() {
              updateSections($(this).val(), null);
          });

          // Sahifa yuklanganda, agar Exam tanlangan bo‘lsa
          var initialExam = $exam.val();
          var initialSection = $section.val();
          if (initialExam) {
              updateSections(initialExam, initialSection);
          }

          // Select2 ni qo‘llash
          if ($.fn.select2) {
              $exam.select2({ width: '100%' });
              $section.select2({ width: '100%' });
          }
      });
  })(django.jQuery);