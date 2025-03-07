<?php
/*
Template Name: Upload Page
*/
get_header(); ?>

<div id="upload-container">
    <h2>Upload Excel Timesheet</h2>
    <form id="upload-form">
        <input type="file" id="file-input" name="file" accept=".xlsx" required>
        <button type="submit">Upload</button>
    </form>
    <p id="message"></p>
</div>

<script>
document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('file-input');
    const file = fileInput.files[0];
    if (!file) {
        document.getElementById('message').innerHTML = 'Please select a file.';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    fetch('http://192.168.168.14:5000/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Upload failed with status: ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        document.getElementById('message').innerHTML = data.message;
        if (data.status === 'success') {
            fileInput.value = ''; // Clear the input after success
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('message').innerHTML = 'Error uploading file: ' + error.message;
    });
});
</script>

<?php get_footer(); ?>