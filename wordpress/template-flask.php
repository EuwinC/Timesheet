<?php
/*
Template Name: Flask Data Page
*/
get_header(); ?>

<div id="flask-data"></div>

<script>
fetch('http://192.168.168.14:5000/api/data')
    .then(response => response.json())
    .then(data => {
        document.getElementById('flask-data').innerHTML = `<p>${data.message}</p>`;
    })
    .catch(error => console.error('Error:', error));
</script>

<?php get_footer(); ?>