<?php
header("Content-Type: application/json");
require_once "db.php";

// Load API Key from "api_key.txt"
$api_key_file = "api_key.txt";
if (!file_exists($api_key_file)) {
    http_response_code(500);
    echo json_encode(["error" => "API key file not found"]);
    exit();
}

$secret_api_key = trim(file_get_contents($api_key_file));

// Validate API Key from request
$headers = getallheaders();
if (!isset($headers['Authorization']) || $headers['Authorization'] !== "Bearer $secret_api_key") {
    http_response_code(403);
    echo json_encode(["error" => "Unauthorized access"]);
    exit();
}

// Handle POST requests to record a visit
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = json_decode(file_get_contents("php://input"), true);

    // Validate input data
    if (!isset($input["dog"]) || !isset($input["start_time"]) || !isset($input["end_time"])) {
        http_response_code(400);
        echo json_encode(["error" => "Invalid input data"]);
        exit();
    }

    // Insert visit into the database
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->prepare("INSERT INTO visits (dog, start_time, end_time) VALUES (:dog, :start_time, :end_time)");
        $stmt->execute([
            ":dog" => $input["dog"],
            ":start_time" => $input["start_time"],
            ":end_time" => $input["end_time"]
        ]);

        echo json_encode(["status" => "success"]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(["error" => $e->getMessage()]);
    }

    exit();
}

// Handle GET requests to fetch recent visits
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    try {
        $pdo = get_db_connection();
        $stmt = $pdo->query("SELECT * FROM visits ORDER BY start_time DESC LIMIT 10");
        $visits = $stmt->fetchAll(PDO::FETCH_ASSOC);

        echo json_encode($visits);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(["error" => $e->getMessage()]);
    }

    exit();
}

// If the request method is not POST or GET, return an error
http_response_code(405);
echo json_encode(["error" => "Method not allowed"]);
?>