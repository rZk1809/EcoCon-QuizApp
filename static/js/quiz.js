document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    const submitBtn = document.getElementById('submit-btn');
    const resultsContainer = document.getElementById('results-container');
    const scoreElement = document.getElementById('score');
    const errorMessageDiv = document.getElementById('error-message');
    let questionsData = []; // Stores questions received from API {id, question, options}

    errorMessageDiv.textContent = ''; // Clear errors on load

    if (typeof currentWeekNumber === 'undefined') {
        console.error("currentWeekNumber is not defined!");
        quizContainer.innerHTML = "<p>Error: Week number not specified.</p>";
        return;
    }

    console.log(`Workspaceing quiz for week ${currentWeekNumber}`);

    fetch(`/api/quiz/${currentWeekNumber}`)
        .then(response => {
            if (!response.ok) {
                 return response.json().then(err => { throw new Error(err.error || `HTTP error! status: ${response.status}`) });
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                 throw new Error(data.error); // Throw error to be caught below
            }
            if (!Array.isArray(data) || data.length === 0) {
                quizContainer.innerHTML = `<p>No questions found or loaded for Week ${currentWeekNumber}. Please try another week or ensure preprocessing is complete.</p>`;
                return; // Stop if no questions
            }
            questionsData = data; // Store questions with their assigned IDs
            renderQuiz(questionsData);
            submitBtn.style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching quiz questions:', error);
            quizContainer.innerHTML = `<p>Failed to load questions for Week ${currentWeekNumber}. Please try again later.</p>`;
            errorMessageDiv.textContent = `Error: ${error.message}`;
        });

    function renderQuiz(mcqs) {
            quizContainer.innerHTML = ''; // Clear loading message
            // Use the loop index + 1 for sequential numbering (1 to 10)
            mcqs.forEach((mcq, index) => {
                const questionDiv = document.createElement('div');
                questionDiv.classList.add('question');
                // Use mcq.id from backend if present, otherwise generate one like q_index
                const questionId = mcq.id || `q_${index}`;
                questionDiv.setAttribute('data-question-id', questionId);
        
                // --- THIS IS THE FIX ---
                // Use "index + 1" for display number, NOT mcq.question_number
                questionDiv.innerHTML = `
                    <p><strong>${index + 1}. ${mcq.question}</strong></p>
                    <div class="options">
                        ${mcq.options.map((option, optionIndex) => `
                            <label>
                                <input type="radio" name="${questionId}" value="${optionIndex}" required>
                                <span>${escapeHtml(option)}</span>  </label><br>
                        `).join('')}
                    </div>
                `;
                // --- END FIX ---
        
                quizContainer.appendChild(questionDiv);
                quizContainer.appendChild(document.createElement('hr'));
            });
        }

    function escapeHtml(text) {
        var map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        const strText = String(text);
        return strText.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    submitBtn.addEventListener('click', () => {
        const answers = {}; // Use object { question_id: selected_index }
        const questions = quizContainer.querySelectorAll('.question');
        let allAnswered = true;
        errorMessageDiv.textContent = ''; // Clear previous errors

        questions.forEach((questionDiv) => {
            const questionId = questionDiv.getAttribute('data-question-id');
            const selectedOption = questionDiv.querySelector(`input[name="${questionId}"]:checked`);
            if (selectedOption) {
                answers[questionId] = parseInt(selectedOption.value, 10);
            } else {
                answers[questionId] = null; // Explicitly mark unanswered
                allAnswered = false;
            }
        });

        if (!allAnswered) {
             errorMessageDiv.textContent = 'Please answer all questions before submitting.';
             return;
         }

        console.log("Submitting answers:", answers);

        fetch('/api/submit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                week_number: currentWeekNumber,
                answers: answers, // Send the answers object
            }),
        })
        .then(response => {
             if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error || `HTTP error! status: ${response.status}`) });
            }
            return response.json();
        })
        .then(result => {
            console.log("Submission result:", result);
            quizContainer.style.display = 'none';
            submitBtn.style.display = 'none';
            scoreElement.textContent = `Your score: ${result.score} / ${result.total_questions}`;
            resultsContainer.style.display = 'block';
        })
        .catch(error => {
            console.error('Error submitting quiz:', error);
            errorMessageDiv.textContent = `Submission failed: ${error.message}`;
            resultsContainer.style.display = 'block'; // Show results area to display error
            scoreElement.textContent = ''; // Clear score display on error
        });
    });
});