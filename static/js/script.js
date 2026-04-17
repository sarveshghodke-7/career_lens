document.getElementById('analyzerForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.textContent = 'Analyzing...';
    submitBtn.disabled = true;

    const formData = new FormData(this);

    try {
        // Sends data to the Flask backend route (e.g., @app.route('/api/analyze'))
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        // Reveal the results section
        document.getElementById('resultsSection').classList.remove('hidden');
        
        // Populate the data
        document.getElementById('atsScore').textContent = data.score;
        
        const matchedList = document.getElementById('matchedKeywords');
        matchedList.innerHTML = '';
        data.matched.forEach(keyword => {
            const li = document.createElement('li');
            li.textContent = keyword;
            matchedList.appendChild(li);
        });

        const missingList = document.getElementById('missingKeywords');
        missingList.innerHTML = '';
        data.missing.forEach(keyword => {
            const li = document.createElement('li');
            li.textContent = keyword;
            missingList.appendChild(li);
        });

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred during analysis.');
    } finally {
        submitBtn.textContent = 'Analyze Resume';
        submitBtn.disabled = false;
    }
});