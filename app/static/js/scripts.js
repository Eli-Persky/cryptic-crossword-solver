document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('clue-form');
    const clueInput = document.getElementById('clue-input');
    const resultContainer = document.getElementById('result-container');

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const clue = clueInput.value;

        if (clue) {
            const response = await fetch('/api/solve', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ clue: clue }),
            });

            if (response.ok) {
                const data = await response.json();
                displayResult(data.solution);
            } else {
                displayError('Error retrieving solution. Please try again.');
            }
        }
    });

    function displayResult(solution) {
        resultContainer.innerHTML = `<p>Solution: ${solution}</p>`;
    }

    function displayError(message) {
        resultContainer.innerHTML = `<p class="error">${message}</p>`;
    }
});