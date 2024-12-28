<?php
// Set the URL to the secure `read_visits.php` endpoint
$api_url = "https://ninas.davidmayman.com/api/read_visits.php";

// Fetch the data from the API
$ch = curl_init($api_url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
$http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

// Handle API errors
if ($http_code !== 200) {
    die("Error fetching visit data. HTTP Status: $http_code");
}

// Decode the JSON response
$visits = json_decode($response, true);
if (json_last_error() !== JSON_ERROR_NONE) {
    die("Error decoding JSON response.");
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visit Data</title>
</head>
<body>
    <h1>Visit Data</h1>
    <?php if (empty($visits)): ?>
        <p>No visit data available.</p>
    <?php else: ?>
        <ul>
            <?php foreach ($visits as $visit): ?>
                <li>
                    Dog: <?php echo htmlspecialchars($visit['dog']); ?><br>
                    Start Time: <?php echo htmlspecialchars($visit['start_time']); ?><br>
                    End Time: <?php echo htmlspecialchars($visit['end_time']); ?><br>
                    Recorded At: <?php echo htmlspecialchars($visit['created_at']); ?>
                </li>
                <br>
            <?php endforeach; ?>
        </ul>
    <?php endif; ?>
</body>
</html>