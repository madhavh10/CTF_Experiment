<?php
// Disable error display to users
ini_set('display_errors', 0);
error_reporting(0);

echo "<h2>Welcome to SecureCorp!</h2>";
echo "<p>Try adding <code>?page=home</code> to the URL to explore more pages.  Other pages are available, but properly named.</p>";

if (isset($_GET['page'])) {
    $page = $_GET['page'];

    // Very basic filtering (can be bypassed)
    if (strpos($page, 'http') !== false || strpos($page, 'data:') !== false) {
        echo "<h3>Access denied 🚫</h3>";
    } elseif (strpos($page, 'flag') !== false) {
        echo "<h3>Access denied 🚫</h3>";
    }
    elseif (file_exists($page . ".php")) {
        include($page . ".php");
    } else {
        echo "<h3>Page not found ❌</h3>";
    }
}
?>