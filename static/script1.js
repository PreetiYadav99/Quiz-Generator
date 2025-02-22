$(document).ready(function () {
    // Handle form submission
    $('#quiz-form').submit(function (e) {
        e.preventDefault();
        let formData = new FormData(this);

        $.ajax({
            url: '/generate',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function (response) {
                if (response.error) {
                    $('#error-message').text(response.error).show();
                    $('#quiz-section').hide();
                } else {
                    $('#error-message').hide();
                    $('#quiz-list').empty();

                    let questions = response.quiz.split('\n').filter(line => line.trim() !== '');
                    let htmlContent = '';
                    questions.forEach((line) => {
                        if (line.startsWith("**Question")) {
                            htmlContent += `<li class="question"><strong>${line.replace(/\*\*/g, '')}</strong></li>`;
                        } else if (line.startsWith("a)") || line.startsWith("b)") || line.startsWith("c)") || line.startsWith("d)")) {
                            htmlContent += `<li class="option" style="margin-left: 20px;">${line}</li>`;
                        } else {
                            htmlContent += `<li>${line}</li>`;
                        }
                    });

                    $('#quiz-list').html(htmlContent);
                    $('#quiz-section').show();
                }
            },
            error: function () {
                $('#error-message').text('An error occurred while generating the quiz.').show();
                $('#quiz-section').hide();
            }
        });
    });

    // Handle PDF download
    $('#download-quiz').click(function () {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Add title
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        doc.text("Generated Quiz", 10, 10);

        // Add each question
        const questions = $('#quiz-list').find('li').toArray();
        let y = 20; // Initial y-position
        questions.forEach((q) => {
            const text = $(q).text();
            doc.text(text, 10, y);
            y += 10; // Increment y-position for each line
            if (y > 280) {  // If y-position exceeds page height
                doc.addPage();
                y = 10;
            }
        });

        // Save the file
        doc.save("quiz.pdf");
    });
});
