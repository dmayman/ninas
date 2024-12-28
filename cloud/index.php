<?php
require_once "api/read_visits.php";

// Fetch the visits using the function
$visits = get_all_visits();
if (isset($visits['error'])) {
    die("Error fetching visit data: " . htmlspecialchars($visits['error']));
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