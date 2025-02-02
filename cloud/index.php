<?php
require_once "api/read_visits.php";

// Set the default time zone to Los Angeles
date_default_timezone_set('America/Los_Angeles');

// Fetch the latest visits for Mila and Nova
$mila_last_visit = get_last_visit("Mila");
$nova_last_visit = get_last_visit("Nova");

// Fetch visits for Mila (past 7 days)
$mila_visits = get_visits_in_past_days('Mila', 7);

// Fetch visits for Nova (past 30 days)
$nova_visits = get_visits_in_past_days('Nova', 30);

// Format the date for display
function format_date($date) {
    $now = new DateTime();
    $date = new DateTime($date);
    $diff = $now->diff($date)->days;

    if ($diff == 0) {
        return "Today, " . $date->format('M j');
    } elseif ($diff == 1) {
        return "Yesterday, " . $date->format('M j');
    } else {
        return $diff . "d ago, " . $date->format('M j');
    }
}

// Format the time for display
function format_time($start_time, $end_time) {
    $utc_timezone = new DateTimeZone('UTC');
    $la_timezone = new DateTimeZone('America/Los_Angeles');

    $start = new DateTime($start_time, $utc_timezone);
    $start->setTimezone($la_timezone);

    $end = new DateTime($end_time, $utc_timezone);
    $end->setTimezone($la_timezone);

    $start_formatted = $start->format('g:ia');
    $end_formatted = $end->format('g:ia');

    if ($start_formatted === $end_formatted) {
        return $start_formatted;
    } else {
        return $start_formatted . " - " . $end_formatted;
    }
}

// Format the duration for display
function format_duration($start_time, $end_time) {
    $duration = strtotime($end_time) - strtotime($start_time);
    if ($duration >= 60) {
        return round($duration / 60) . "m";
    } else {
        return $duration . "s";
    }
}

?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Lexend+Deca:wght@100..900&family=Lexend+Peta&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="styles.css">
    <title>Mila and Nova</title>
</head>
<body>
    <div class="page-wrapper">
        <!-- Mila's Column -->
        <div class="column mila">
            <div class="main-section">    
                <div class="dog-name">Mila</div>
                <div class="dog-emoji"><img src="static/milamoji.png"></div>
                <div class="info">Last eaten</div>
                <div class="time" id="mila-last-eaten">
                    Loading...
                </div>
                <div class="info" id="mila-visit-time">
                    Loading...
                </div>
                <div class="arrow">
                    <img src="static/mila-arrow.svg" alt="Down Arrow">
                </div>
            </div>
            <div class="chart-section">
                <div class="chart">
                    <div class="info">Past 7 days</div>
                    <?php foreach ($mila_visits as $visit): ?>
                        <div class="chart-row">
                            <span class="chart-date"><?= format_date($visit['start_time']) ?></span>
                            <span class="chart-time"><?= format_time($visit['start_time'], $visit['end_time']) ?></span>
                            <span class="chart-duration"><?= format_duration($visit['start_time'], $visit['end_time']) ?></span>
                        </div>
                    <?php endforeach; ?>
                </div> 
            </div>
        </div>

        <!-- Nova's Column -->
        <div class="column nova">
            <div class="main-section">    
                <div class="dog-name">Nova</div>
                <div class="dog-emoji"><img src="static/novamoji.png"></div>
                <div class="info">Last stolen</div>
                <div class="time" id="nova-last-stolen">
                    Loading...
                </div>
                <div class="info" id="nova-visit-time">
                    Loading...
                </div>
                <div class="arrow">
                    <img src="static/nova-arrow.svg" alt="Down Arrow">
                </div>
            </div>
            <div class="chart-section">
                <div class="chart">
                    <div class="info">Past 30 days</div>
                    <?php foreach ($nova_visits as $visit): ?>
                        <div class="chart-row">
                            <span class="chart-date"><?= format_date($visit['start_time']) ?></span>
                            <span class="chart-time"><?= format_time($visit['start_time'], $visit['end_time']) ?></span>
                            <span class="chart-duration"><?= format_duration($visit['start_time'], $visit['end_time']) ?></span>
                        </div>
                    <?php endforeach; ?>
                </div> 
            </div>
        </div>
    </div>
    <script>
        // Data from the server
        const milaLastVisit = <?= json_encode($mila_last_visit) ?>;
        const novaLastVisit = <?= json_encode($nova_last_visit) ?>;

        // Convert UTC datetime to local time and format it
        function formatRelativeTime(utcString) {
            const utcDate = new Date(utcString + "Z"); // Ensure UTC interpretation
            const now = new Date();
            const diff = Math.abs(now - utcDate);
            const diffMinutes = Math.floor(diff / 1000 / 60);
            const diffHours = Math.floor(diffMinutes / 60);
            const days = Math.floor(diffHours / 24);
            const hours = diffHours % 24;
            const minutes = diffMinutes % 60;

            const parts = [];
            if (days > 0) parts.push(`${days}d`);
            if (hours > 0) parts.push(`${hours}h`);
            if (minutes > 0) parts.push(`${minutes}m`);

            return parts.join(" ") + " ago";
        }

        function formatAbsoluteTime(utcStart, utcEnd) {
            const start = new Date(utcStart + "Z").toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
            const end = new Date(utcEnd + "Z").toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });

            if (start === end) {
                return start;
            } else {
                return `${start} - ${end}`;
            }
        }

        // Update Mila's Data
        if (milaLastVisit && milaLastVisit.end_time) {
            document.getElementById("mila-last-eaten").textContent = formatRelativeTime(milaLastVisit.end_time);
        } else {
            document.getElementById("mila-last-eaten").textContent = "No data";
        }

        if (milaLastVisit && milaLastVisit.start_time && milaLastVisit.end_time) {
            document.getElementById("mila-visit-time").textContent = formatAbsoluteTime(milaLastVisit.start_time, milaLastVisit.end_time);
        } else {
            document.getElementById("mila-visit-time").textContent = "No data";
        }

        // Update Nova's Data
        if (novaLastVisit && novaLastVisit.end_time) {
            document.getElementById("nova-last-stolen").textContent = formatRelativeTime(novaLastVisit.end_time);
        } else {
            document.getElementById("nova-last-stolen").textContent = "No data";
        }

        if (novaLastVisit && novaLastVisit.start_time && novaLastVisit.end_time) {
            document.getElementById("nova-visit-time").textContent = formatAbsoluteTime(novaLastVisit.start_time, novaLastVisit.end_time);
        } else {
            document.getElementById("nova-visit-time").textContent = "No data";
        }

        document.addEventListener("scroll", () => {
            const arrows = document.querySelectorAll(".arrow");
            if (window.scrollY > 20) {
                arrows.forEach(arrow => arrow.classList.add("hidden"));
            } else {
                arrows.forEach(arrow => arrow.classList.remove("hidden"));
            }
        });
    </script>
</body>
</html>