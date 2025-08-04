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
        
        // Determine if we're in mock mode based on the URL path or a global variable
        const isMockMode = window.location.pathname === '/mock' || window.mockMode === true;
        
        // In mock mode, allow empty clue (we'll use the clue from mock data)
        // In normal mode, require a clue
        if (!isMockMode && !clue) return;

        showLoading();
        hideResults();

        try {
            const endpoint = isMockMode ? '/api/submit_clue_mock' : '/api/submit_clue';
            const requestBody = { clue: clue, length: solutionLength };

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
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

    // Interactive Clue functionality
    function setupInteractiveClue(clue, wordMapping) {
        const interactiveClueContainer = document.getElementById('interactive-clue');
        const words = clue.split(/\s+/);
        
        interactiveClueContainer.innerHTML = '';
        
        words.forEach((word, index) => {
            const wordSpan = document.createElement('span');
            wordSpan.className = 'clue-word';
            wordSpan.textContent = word;
            wordSpan.dataset.position = index;
            
            // Add role class if word has mapping
            if (wordMapping && wordMapping[index]) {
                const mapping = wordMapping[index];
                wordSpan.classList.add(`role-${mapping.role}`);
                
                // Add hover event listeners
                wordSpan.addEventListener('mouseenter', (e) => showTooltip(e, mapping, index, wordMapping));
                wordSpan.addEventListener('mouseleave', hideTooltip);
            }
            
            interactiveClueContainer.appendChild(wordSpan);
            
            // Add space after word (except last word)
            if (index < words.length - 1) {
                interactiveClueContainer.appendChild(document.createTextNode(' '));
            }
        });
        
        // Add legend
        addClueRoleLegend();
    }
    
    function showTooltip(event, mapping, position, wordMapping) {
        hideTooltip(); // Hide any existing tooltips
        
        const tooltips = [];
        
        // Primary tooltip for the hovered word (always above)
        const primaryTooltip = createTooltip(mapping, 'primary-tooltip');
        tooltips.push({
            element: primaryTooltip, 
            mapping: mapping, 
            position: position,
            targetElement: event.target,
            placement: 'above'
        });
        
        // Check if this word has a related indicator/target pair
        let relatedMapping = null;
        let relatedElement = null;
        if (mapping.related_positions && mapping.related_positions.length > 0) {
            // Find the first related word that has a different role
            for (const relatedPos of mapping.related_positions) {
                if (wordMapping[relatedPos] && wordMapping[relatedPos].role !== mapping.role) {
                    relatedMapping = wordMapping[relatedPos];
                    relatedElement = document.querySelector(`[data-position="${relatedPos}"]`);
                    break;
                }
            }
            
            if (relatedMapping && relatedElement) {
                const secondaryTooltip = createTooltip(relatedMapping, 'secondary-tooltip');
                tooltips.push({
                    element: secondaryTooltip, 
                    mapping: relatedMapping, 
                    position: relatedMapping.position,
                    targetElement: relatedElement,
                    placement: 'below'
                });
            }
        }
        
        // Add tooltips to DOM and position them
        tooltips.forEach((tooltip, index) => {
            document.body.appendChild(tooltip.element);
            positionTooltip(tooltip.targetElement, tooltip.element, tooltip.placement);
            
            // Animate in
            setTimeout(() => {
                tooltip.element.classList.add('show');
            }, 10);
        });
        
        // Highlight current word with role-specific styling
        event.target.classList.add('highlighted');
        
        // Highlight related words with role-specific styling
        if (mapping.related_positions) {
            mapping.related_positions.forEach(relatedPos => {
                const relatedWord = document.querySelector(`[data-position="${relatedPos}"]`);
                if (relatedWord) {
                    relatedWord.classList.add('related-highlighted');
                }
            });
        }
    }
    
    function createTooltip(mapping, tooltipClass) {
        const tooltip = document.createElement('div');
        tooltip.className = `word-tooltip ${tooltipClass}`;
        
        let typeInfo = '';
        if (mapping.type && mapping.type !== mapping.wordplay_type) {
            typeInfo = `<div class="tooltip-type">${mapping.type}</div>`;
        } else if (mapping.wordplay_type && mapping.wordplay_type !== 'none') {
            typeInfo = `<div class="tooltip-type">${mapping.wordplay_type}</div>`;
        }
        
        let resultInfo = '';
        if (mapping.result && mapping.result.trim() !== '') {
            resultInfo = `<div class="tooltip-result">${mapping.result}</div>`;
        }
        
        tooltip.innerHTML = `
            <div class="tooltip-role">${mapping.role.charAt(0).toUpperCase() + mapping.role.slice(1)}</div>
            ${typeInfo}
            <div class="tooltip-description">${mapping.description}</div>
            ${resultInfo}
        `;
        
        return tooltip;
    }
    
    function positionTooltip(targetElement, tooltip, placement) {
        const rect = targetElement.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
        
        let top, left;
        const tooltipHeight = tooltipRect.height || 120; // Estimated height
        
        // Horizontal positioning - center the tooltip on the word
        left = rect.left + scrollLeft + (rect.width / 2) - 150; // 150 = half of 300px max-width
        
        // Ensure tooltip doesn't go off the left edge
        if (left < 10) {
            left = 10;
        }
        
        // Ensure tooltip doesn't go off the right edge
        const tooltipWidth = 300; // Max width from CSS
        if (left + tooltipWidth > window.innerWidth - 10) {
            left = window.innerWidth - tooltipWidth - 10;
        }
        
        // Vertical positioning based on placement
        if (placement === 'above') {
            top = rect.top + scrollTop - tooltipHeight - 10;
            tooltip.classList.add('tooltip-above');
            
            // If not enough space above, force it above anyway but adjust if needed
            if (top < 10) {
                top = 10;
            }
        } else { // placement === 'below'
            top = rect.bottom + scrollTop + 10;
            tooltip.classList.add('tooltip-below');
            
            // If not enough space below, keep it below but adjust if needed
            if (top + tooltipHeight > viewportHeight + scrollTop - 10) {
                top = viewportHeight + scrollTop - tooltipHeight - 10;
            }
        }
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
        
        // Adjust arrow position to point to the center of the target word
        const arrow = tooltip.querySelector('::after') || tooltip;
        const arrowOffset = rect.left + scrollLeft + (rect.width / 2) - left - 20; // 20 is default arrow position
        if (arrowOffset > 10 && arrowOffset < tooltipWidth - 20) {
            // Only adjust if the arrow would be within reasonable bounds
            tooltip.style.setProperty('--arrow-offset', `${arrowOffset}px`);
        }
    }
    
    function hideTooltip() {
        // Find and animate out existing tooltips
        const existingTooltips = document.querySelectorAll('.word-tooltip');
        existingTooltips.forEach(tooltip => {
            tooltip.classList.remove('show');
            // Remove after animation completes
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 200);
        });
        
        // Remove all highlight classes
        document.querySelectorAll('.clue-word').forEach(word => {
            word.classList.remove('highlighted', 'related-highlighted');
        });
    }
    
    function addClueRoleLegend() {
        const legendContainer = document.querySelector('.clue-legend');
        if (!legendContainer) {
            const legend = document.createElement('div');
            legend.className = 'clue-legend';
            legend.innerHTML = `
                <div class="legend-item">
                    <div class="legend-color definition"></div>
                    <span>Definition</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color indicator"></div>
                    <span>Indicator</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color target"></div>
                    <span>Target</span>
                </div>
            `;
            
            const interactiveSection = document.querySelector('.interactive-clue-section');
            if (interactiveSection) {
                interactiveSection.appendChild(legend);
            }
        }
    }

    function displaySolution(formattedClue, originalClue, solution) {
        // Display main solution
        const completeSolution = solution.complete_solution;
        document.getElementById('main-answer').textContent = completeSolution.solution || 'Unknown';
        
        // Setup interactive clue if word mapping is available
        if (solution.interactive_clue && solution.interactive_clue.word_mapping) {
            const interactiveSection = document.querySelector('.interactive-clue-section');
            if (interactiveSection) {
                interactiveSection.classList.remove('hidden');
                const displayClue = solution.interactive_clue.original_clue;
                setupInteractiveClue(displayClue, solution.interactive_clue.word_mapping);
            }
        } else {
            const interactiveSection = document.querySelector('.interactive-clue-section');
            if (interactiveSection) {
                interactiveSection.classList.add('hidden');
            }
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
                    ${attempt.solution ? `<div><strong>Solution:</strong> ${attempt.solution}</div>` : ''}
                    ${attempt.definition ? `<div><strong>Definition:</strong> ${attempt.definition}</div>` : ''}
                    <div class="attempt-components">
                        ${attempt.wordplay_components.map(comp => {
                            let componentText = `${comp.indicator} (${comp.wordplay_type})`;
                            if (comp.target && comp.result) {
                                componentText += ` → ${comp.target}: ${comp.result}`;
                            } else if (comp.result) {
                                componentText += `: ${comp.result}`;
                            }
                            return `<span class="mini-component">${componentText}</span>`;
                        }).join(' ')}
                    </div>
                `;
                attemptsList.appendChild(attemptDiv);
            });
            attemptsSection.classList.remove('hidden');
        } else {
            attemptsSection.classList.add('hidden');
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