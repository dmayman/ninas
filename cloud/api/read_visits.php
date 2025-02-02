<?php
require_once "db.php";

// Fetch the last visit for a specific dog
function get_last_visit($dog) {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->prepare("SELECT * FROM visits WHERE dog = :dog ORDER BY end_time DESC LIMIT 1");
        $stmt->execute(['dog' => $dog]);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        return ["error" => $e->getMessage()];
    }
}

// Fetch all visits for a specific dog in the past Y days
function get_visits_in_past_days($dog, $days) {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->prepare("SELECT * FROM visits WHERE dog = :dog AND end_time >= NOW() - INTERVAL :days DAY ORDER BY end_time DESC");
        $stmt->execute(['dog' => $dog, 'days' => $days]);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        return ["error" => $e->getMessage()];
    }
}

// Helper function for relative time
function time_elapsed_string($datetime) {
    $now = new DateTime();
    $ago = new DateTime($datetime);
    $diff = $now->diff($ago);

    $parts = [];
    if ($diff->d > 0) $parts[] = $diff->d . "d";
    if ($diff->h > 0) $parts[] = $diff->h . "h";
    if ($diff->i > 0) $parts[] = $diff->i . "m";

    return implode(" ", $parts) . " ago";
}


?>