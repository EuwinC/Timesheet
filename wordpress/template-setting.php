<?php
/*
Template Name: Settings Page
*/
get_header(); ?>

<div id="settings">
    <div id="employees"></div>
    <input type="text" id="new_person_name" placeholder="Name">
    <input type="text" id="new_person_staff_number" placeholder="Staff Number">
    <button onclick="addPerson()">Add Person</button>
</div>

<script>
fetch('http://192.168.168.14:5000/api/settings', { credentials: 'include' })
    .then(response => response.json())
    .then(data => {
        if (data.error) window.location.href = '/home';
        document.getElementById('employees').innerHTML = JSON.stringify(data.people_list);
    });
function addPerson() {
    fetch('http://192.168.168.14:5000/api/add_person', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            new_person_name: document.getElementById('new_person_name').value,
            new_person_staff_number: document.getElementById('new_person_staff_number').value
        }),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => alert(data.message));
}
</script>

<?php get_footer(); ?>