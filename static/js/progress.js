document.addEventListener('DOMContentLoaded', () => {
    const progressList = document.getElementById('progress-list');
    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.textContent = ''; // Clear error

    fetch('/api/progress')
        .then(response => {
             if (!response.ok) {
                 return response.json().then(err => { throw new Error(err.error || `HTTP error! status: ${response.status}`) });
            }
            return response.json();
        })
        .then(data => {
            progressList.innerHTML = ''; // Clear loading message
            if (data.error) {
                 throw new Error(data.error);
            }
            if (!Array.isArray(data) || data.length === 0) {
                 progressList.innerHTML = '<p>No quiz attempts found yet.</p>';
                 return;
            }

            const table = document.createElement('table');
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>Score</th>
                        <th>Percentage</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.map(attempt => `
                        <tr>
                            <td>${attempt.week}</td>
                            <td>${attempt.score} / ${attempt.total}</td>
                            <td>${attempt.percentage}%</td>
                            <td>${attempt.timestamp}</td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            progressList.appendChild(table);
        })
        .catch(error => {
            console.error('Error fetching progress:', error);
            progressList.innerHTML = '<p>Failed to load progress. Please try again later.</p>';
            errorMessageDiv.textContent = `Error: ${error.message}`;
        });
});