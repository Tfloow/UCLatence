function sendChoice(choice, service) {
    // Send an HTTP request to the server with the user's choice
    fetch(`/process?choice=${choice}&service=${service}`)
        .then(response => response.text())
        .then(result => {
            // Update the content below the buttons with the server's response
            document.getElementById('result').innerHTML = result;
        })
        .catch(error => console.error('Error:', error));
}