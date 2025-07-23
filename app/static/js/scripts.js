document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('clue-form');
    const clueInput = document.getElementById('clue');
    const lengthInput = document.getElementById('solution-length');
    const loading = document.getElementById('loading');
    const errorDisplay = document.getElementById('error-display');
    const solutionDisplay = document.getElementById('solution-display');

    // Handle form submission
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        await solveClue();
    });

    async function solveClue() {
        let clue = clueInput.value.trim();
        const solutionLength = lengthInput.value;
        
        if (!clue) return;

        showLoading();
        hideResults();

        try {
            const response = await fetch('/api/submit_clue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ clue: clue, length: solutionLength })
            });

            const data = await response.json();

            if (response.ok) {
                // Pass both the clue and original clue for display
                displaySolution(clue, clueInput.value.trim(), data.solution);
            } else {
                displayError(data.error || 'Error retrieving solution');
            }
        } catch (error) {
            displayError('Network error. Please try again.');
        } finally {
            hideLoading();
        }
    }

    function displaySolution(formattedClue, originalClue, solution) {
        // Display the original clue (without length) for better readability
        document.getElementById('result-clue').textContent = originalClue;
        
        // Show length information if it was provided
        const lengthInput = document.getElementById('solution-length');
        const lengthInfo = document.getElementById('length-info');
        const expectedLength = document.getElementById('expected-length');
        
        if (lengthInput.value && lengthInput.value >= 3) {
            expectedLength.textContent = lengthInput.value;
            lengthInfo.classList.remove('hidden');
        } else {
            lengthInfo.classList.add('hidden');
        }
        
        // Display main solution
        const completeSolution = solution.complete_solution;
        document.getElementById('main-answer').textContent = completeSolution.solution || 'Unknown';
        
        // Display definition
        document.getElementById('definition-text').textContent = completeSolution.definition || 'Not provided';
        
        // Display wordplay components
        const componentsContainer = document.getElementById('wordplay-components');
        componentsContainer.innerHTML = '';
        
        if (completeSolution.wordplay_components && completeSolution.wordplay_components.length > 0) {
            completeSolution.wordplay_components.forEach((component, index) => {
                const componentDiv = document.createElement('div');
                componentDiv.className = 'wordplay-component';
                componentDiv.innerHTML = `
                    <div class="component-header">
                        <span class="component-number">${index + 1}</span>
                        <span class="component-type">${component.wordplay_type}</span>
                    </div>
                    <div class="component-details">
                        <div><strong>Indicator:</strong> "${component.indicator}"</div>
                        ${component.target ? `<div><strong>Target:</strong> "${component.target}"</div>` : ''}
                    </div>
                `;
                componentsContainer.appendChild(componentDiv);
            });
        } else {
            componentsContainer.innerHTML = '<div class="no-components">No wordplay components identified</div>';
        }

        // Display attempted solutions if any
        const attemptsSection = document.getElementById('attempts-section');
        const attemptsList = document.getElementById('attempts-list');
        
        if (solution.attempted_solutions && solution.attempted_solutions.length > 0) {
            attemptsList.innerHTML = '';
            solution.attempted_solutions.forEach((attempt, index) => {
                const attemptDiv = document.createElement('div');
                attemptDiv.className = 'attempt-item';
                attemptDiv.innerHTML = `
                    <h4>Attempt ${index + 1}</h4>
                    ${attempt.solution ? `<div><strong>Partial Solution:</strong> ${attempt.solution}</div>` : ''}
                    ${attempt.definition ? `<div><strong>Definition:</strong> ${attempt.definition}</div>` : ''}
                    <div class="attempt-components">
                        ${attempt.wordplay_components.map(comp => 
                            `<span class="mini-component">${comp.indicator} (${comp.wordplay_type})</span>`
                        ).join(' ')}
                    </div>
                `;
                attemptsList.appendChild(attemptDiv);
            });
            attemptsSection.classList.remove('hidden');
        } else {
            attemptsSection.classList.add('hidden');
        }

        // Display reasoning analysis if available
        const reasoningSection = document.getElementById('reasoning-section');
        const reasoningText = document.getElementById('reasoning-text');
        const toggleButton = document.getElementById('toggle-reasoning');
        
        if (solution.reasoning_analysis) {
            reasoningText.textContent = solution.reasoning_analysis;
            reasoningSection.classList.remove('hidden');
            
            // Add toggle functionality
            toggleButton.addEventListener('click', function() {
                const isVisible = !reasoningText.classList.contains('hidden');
                if (isVisible) {
                    reasoningText.classList.add('hidden');
                    toggleButton.textContent = 'Show Reasoning';
                } else {
                    reasoningText.classList.remove('hidden');
                    toggleButton.textContent = 'Hide Reasoning';
                }
            });
            
            // Initially hide the reasoning text
            reasoningText.classList.add('hidden');
        } else {
            reasoningSection.classList.add('hidden');
        }

        solutionDisplay.classList.remove('hidden');
    }

    function displayError(message) {
        errorDisplay.textContent = message;
        errorDisplay.classList.remove('hidden');
    }

    function showLoading() {
        loading.classList.remove('hidden');
    }

    function hideLoading() {
        loading.classList.add('hidden');
    }

    function hideResults() {
        errorDisplay.classList.add('hidden');
        solutionDisplay.classList.add('hidden');
    }
});