<?php
// Disable error display to users
ini_set('display_errors', 0);
error_reporting(0);

echo "<h2>Welcome to SecureCorp!</h2>";
echo "<p>Try adding <code>?page=</code> to the URL to explore more pages.</p>";

function sanitizeFilename($filename) {
    $filename = preg_replace('/[^a-zA-Z0-9_\-\.]/', '', $filename);
    return $filename;
}

if (isset($_GET['page'])) {
    $page = $_GET['page'];

    // Very basic filtering (can be bypassed)
    if (strpos($page, 'http') !== false || strpos($page, 'data:') !== false) {
        echo "<h3>Access denied 🚫</h3>";
    } else {
        $sanitizedPage = sanitizeFilename($page);
        if ($sanitizedPage != $page) {
           echo "<h3>Invalid filename 🚫</h3>";
        }
        else {
            $filePath = "pages/" . $sanitizedPage;
            if (file_exists($filePath)) {
                include($filePath);
            } else {
                echo "<h3>Page not found ❌</h3>";
            }
        }

    }
}
?>