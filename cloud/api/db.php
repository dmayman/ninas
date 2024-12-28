<?php
// Database configuration
$host = "localhost";
$dbname = "hgzywhmy_ninas";
$username = "hgzywhmy_ninas";
$password = "MilaNovaNinas";

function get_db_connection() {
    global $host, $dbname, $username, $password;

    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    return $pdo;
}
?>