// Wait for the DOM to load before executing any code
document.addEventListener('DOMContentLoaded', function() {
    // Get references to various DOM elements
    const container = document.getElementById('rdfDataContainer');
    const articleInfoContainer = document.getElementById('articleInfoContainer');
    const questionBox = document.getElementById('questionBox');
    const totalScoreElement = document.getElementById('totalScore');

    // Function to handle the submission of an answer
    function handleSubmit() {
        // Get the selected option from the radio buttons
        const selectedOption = document.querySelector('input[name="answer"]:checked');
        if (!selectedOption) {
            alert('Please select an option.');  // Alert if no option is selected
            return;
        }

        // Determine the score based on the selected option
        let score;
        switch (selectedOption.value) {
            case '(i)':
                score = 0;
                break;
            case '(ii)':
                score = 1;
                break;
            case '(iii)':
                score = 2;
                break;
            default:
                score = 0;
                break;
        }

        // Send the selected answer and score to the server
        fetch('/submit_answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ choice: selectedOption.value, score: score })
        })
        .then(response => response.json())
        .then(data => {
            // Update the total score displayed on the page
            totalScoreElement.textContent = data.total_score;

            // Check if the quiz is completed
            if (data.completed) {
                // Redirect to the completion page
                window.location.href = '/complete';
            } else {
                // Load the next question
                loadNextQuestion();
            }
        })
        .catch(error => {
            console.error('Error submitting answer:', error);
        });
    }

    // Function to attach event listener to the submit button
    function attachSubmitButtonListener() {
        const submitButton = document.getElementById('submitButton');
        submitButton.addEventListener('click', handleSubmit);
    }

    // Function to load the next question from the server
    function loadNextQuestion() {
        fetch('/get_next_question')
        .then(response => response.json())
        .then(data => {
            // Update the UI with the new question and article info
            updateQuestionUI(data);
            updateArticleInfo(data.article_details);
        })
        .catch(error => {
            console.error('Error loading next question:', error);
        });
    }

    // Function to update the question UI with new data
    function updateQuestionUI(data) {
        questionBox.innerHTML = `
            <div class="question-header">
                <h3>Multiple Choice Question #${data.question.number}</h3>
                <p>${data.question.definition}</p>
            </div>
        `;

        container.innerHTML = `
            <form id="answerForm">
                <ul>
                    ${data.answers.map(answer => `
                        <li>
                            <input type="radio" name="answer" value="${answer.answerLabel}" data-score="${answer.score}">
                            ${answer.answerLabel}: ${answer.answerDef}
                        </li>
                    `).join('')}
                </ul>
            </form>
        `;
    }

    // Function to update the article info section with new data
    function updateArticleInfo(articleDetails) {
        articleInfoContainer.innerHTML = `
            <div class="article-info-box-left">
                <h3>${articleDetails.prefLabel}</h3>
                <p>${articleDetails.definition}</p>
            </div>
            <div class="article-info-box-right">
                <p>Source: <a href="${articleDetails.source}">${articleDetails.source}</a></p>
                <p>Score: <span id="totalScore">${totalScoreElement.textContent}</span></p>
            </div>
        `;
    }

    // Attach event listener to the submit button and load the first question
    attachSubmitButtonListener();
    loadNextQuestion();
});
