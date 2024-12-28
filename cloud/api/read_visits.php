<?php
header("Content-Type: application/json");
require_once "db.php"; // Ensure this file contains the database connection logic

// Function to fetch all visits from the database
function get_all_visits() {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->query("SELECT * FROM visits ORDER BY start_time DESC");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        http_response_code(500);
        return ["error" => $e->getMessage()];
    }
}

// If this file is accessed directly, output the visits as JSON
if (basename($_SERVER['PHP_SELF']) === basename(__FILE__)) {
    echo json_encode(get_all_visits(), JSON_PRETTY_PRINT);
}
?>