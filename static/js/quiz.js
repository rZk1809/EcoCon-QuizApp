// static/js/quiz.js
document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quiz-container');
    const submitBtn = document.getElementById('submit-btn');
    const resultsContainer = document.getElementById('results-container');
    const scoreElement = document.getElementById('score');
    const errorMessageDiv = document.getElementById('error-message');
    const detailedResultsList = document.getElementById('detailed-results-list'); // Get the new list element
    let questionsData = [];

    errorMessageDiv.textContent = '';

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
            if (data.error) { throw new Error(data.error); }
            if (!Array.isArray(data) || data.length === 0) {
                quizContainer.innerHTML = `<p>No questions found or loaded for Week ${currentWeekNumber}.</p>`;
                return;
            }
            questionsData = data;
            renderQuiz(questionsData);
            submitBtn.style.display = 'block';
        })
        .catch(error => {
            console.error('Error fetching quiz questions:', error);
            quizContainer.innerHTML = `<p>Failed to load questions for Week ${currentWeekNumber}.</p>`;
            errorMessageDiv.textContent = `Error: ${error.message}`;
        });

    function renderQuiz(mcqs) {
        quizContainer.innerHTML = '';
        mcqs.forEach((mcq, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('question');
            const questionId = mcq.id || `q_${index}`; // Use ID from backend
            questionDiv.setAttribute('data-question-id', questionId);
            questionDiv.innerHTML = `
                <p><strong>${index + 1}. ${mcq.question}</strong></p> <div class="options">
                    ${mcq.options.map((option, optionIndex) => `
                        <label>
                            <input type="radio" name="${questionId}" value="${optionIndex}" required>
                            <span>${escapeHtml(option)}</span>
                        </label><br>
                    `).join('')}
                </div>
            `;
            quizContainer.appendChild(questionDiv);
             // Add hr only between questions if desired
             if (index < mcqs.length - 1) {
                 quizContainer.appendChild(document.createElement('hr'));
             }
        });
    }

    function escapeHtml(text) {
        var map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        const strText = String(text); // Ensure it's a string
        return strText.replace(/[&<>"']/g, function(m) { return map[m]; });
    }

    submitBtn.addEventListener('click', () => {
        const answers = {};
        const questions = quizContainer.querySelectorAll('.question');
        let allAnswered = true;
        errorMessageDiv.textContent = '';

        questions.forEach((questionDiv) => {
            const questionId = questionDiv.getAttribute('data-question-id');
            const selectedOption = questionDiv.querySelector(`input[name="${questionId}"]:checked`);
            if (selectedOption) {
                answers[questionId] = parseInt(selectedOption.value, 10);
            } else {
                answers[questionId] = null;
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
            body: JSON.stringify({ week_number: currentWeekNumber, answers: answers }),
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
            errorMessageDiv.textContent = ''; // Clear errors on success

            // Display score
            scoreElement.textContent = `Your score: ${result.score} / ${result.total_questions}`;

            // --- Render Detailed Results ---
            detailedResultsList.innerHTML = ''; // Clear previous results
            if (result.results && Array.isArray(result.results)) {
                result.results.forEach((item, index) => {
                    const mainLi = document.createElement('li');
                    mainLi.classList.add('result-item');
                    if (!item.is_correct) {
                        mainLi.classList.add('incorrect-result'); // Optional class for wrong answers
                    }

                    // Question Text
                    const questionP = document.createElement('p');
                    questionP.innerHTML = `<strong>${index + 1}. ${escapeHtml(item.question_text)}</strong>`;
                    mainLi.appendChild(questionP);

                    // Options List
                    const optionsUl = document.createElement('ul');
                    optionsUl.classList.add('result-options');
                    const options = item.options || []; // Default to empty array
                    const letters = ['A', 'B', 'C', 'D'];

                    options.forEach((option, optionIndex) => {
                        const optionLi = document.createElement('li');
                        let prefix = letters[optionIndex] ? `${letters[optionIndex]}. ` : '';
                        optionLi.innerHTML = `${prefix}${escapeHtml(option)}`;

                        // Highlight correct answer
                        if (optionIndex === item.correct_option_index) {
                            optionLi.classList.add('correct-answer');
                            optionLi.innerHTML += ' ✔️ (Correct)'; // Add checkmark
                        }
                        // Highlight user's answer
                        if (optionIndex === item.selected_option_index) {
                            optionLi.classList.add('user-answer');
                             if (!item.is_correct) {
                                 optionLi.innerHTML += ' ❌ (Your Answer)'; // Add cross mark if wrong
                             }
                        } else if (item.selected_option_index === null && optionIndex === item.correct_option_index) {
                             // If unanswered, still clearly mark the correct one
                             // Already handled by adding "(Correct)" above
                        }

                        optionsUl.appendChild(optionLi);
                    });

                    // Handle unanswered case
                    if (item.selected_option_index === null) {
                         const unansweredP = document.createElement('p');
                         unansweredP.classList.add('unanswered-info');
                         unansweredP.textContent = ' (You did not answer this question)';
                         mainLi.appendChild(unansweredP);
                    }


                    mainLi.appendChild(optionsUl);
                    detailedResultsList.appendChild(mainLi);
                });
            }
             // --- End Render Detailed Results ---

            resultsContainer.style.display = 'block'; // Show the whole results section
        })
        .catch(error => {
            console.error('Error submitting quiz:', error);
            errorMessageDiv.textContent = `Submission failed: ${error.message}`;
            // Optionally hide quiz/button and show results container to display error
            // quizContainer.style.display = 'none';
            // submitBtn.style.display = 'none';
            // resultsContainer.style.display = 'block';
            // scoreElement.textContent = '';
        });
    });
});