<?php
/*
Template Name: Home Page
*/
get_header(); ?>

<div id="login-form">
    <input type="text" id="user_id" placeholder="User ID">
    <input type="password" id="password" placeholder="Password">
    <button onclick="login()">Login</button>
    <button onclick="register()">Register</button>
    <p id="message"></p>
</div>

<script>
function login() {
    fetch('http://192.168.168.14:5000/api/home', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: document.getElementById('user_id').value, password: document.getElementById('password').value }),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('message').innerHTML = data.message;
        if (data.status === 'success') window.location.href = '/dashboard';
    });
}
function register() {
    fetch('http://192.168.168.14:5000/api/home', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New User', user_id: document.getElementById('user_id').value, password: document.getElementById('password').value }),
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => document.getElementById('message').innerHTML = data.message);
}
</script>

<?php get_footer(); ?>