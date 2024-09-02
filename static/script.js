const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const message = document.getElementById('message');
const spinner = document.getElementById('spinner');
const results = document.getElementById('results');
const historicalChart = document.getElementById('historicalChart');
const forecastChart = document.getElementById('forecastChart');
const forecastTableBody = document.getElementById('forecastTableBody');

function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.remove('d-none', 'alert-success', 'alert-danger');
    message.classList.add(isError ? 'alert-danger' : 'alert-success');
}

uploadBtn.addEventListener('click', () => {
    const file = fileInput.files[0];
    if (!file) {
        showMessage('Please select a file first.', true);
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showMessage('');
    spinner.classList.remove('d-none');
    results.classList.remove('show');
    results.classList.add('d-none');

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        spinner.classList.add('d-none');
        if (data.error) {
            showMessage(data.error, true);
        } else {
            showMessage(data.message);
            
            historicalChart.src = `data:image/png;base64,${data.historical_chart}`;
            forecastChart.src = `data:image/png;base64,${data.forecast_chart}`;

            forecastTableBody.innerHTML = '';
            data.forecast_data.forEach(item => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${item.date}</td>
                    <td>${item.value.toFixed(2)}</td>
                `;
                forecastTableBody.appendChild(row);
            });

            results.classList.remove('d-none');
            setTimeout(() => results.classList.add('show'), 50);
        }
    })
    .catch(error => {
        spinner.classList.add('d-none');
        showMessage('An error occurred during upload.', true);
        console.error('Error:', error);
    });
});