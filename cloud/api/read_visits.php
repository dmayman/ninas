<?php
header("Content-Type: application/json");
require_once "db.php"; // Ensure this file contains the database connection logic

// Fetch all visits from the database
try {
    $pdo = get_db_connection();
    $stmt = $pdo->query("SELECT * FROM visits ORDER BY start_time DESC");
    $visits = $stmt->fetchAll(PDO::FETCH_ASSOC);

    echo json_encode($visits, JSON_PRETTY_PRINT);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(["error" => $e->getMessage()]);
}
?>