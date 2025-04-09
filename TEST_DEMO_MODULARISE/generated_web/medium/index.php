<?php
// Disable error display to users
ini_set('display_errors', 0);
error_reporting(0);

echo "<h2>Welcome to SecureCorp!</h2>";
echo "<p>Try adding <code>?page=</code> to the URL to explore more pages.</p>";

if (isset($_GET['page'])) {
    $page = $_GET['page'];

    // Very basic filtering (can be bypassed)
    if (strpos($page, 'http') !== false || strpos($page, 'data:') !== false) {
        echo "<h3>Access denied 🚫</h3>";
    } else {
        $allowed_pages = array('home.php', 'about.php'); // Add a whitelist
        if(in_array($page, $allowed_pages)) {
            include($page);
        } else if (strpos($page, '.') === false) {
             include($page . '.php');
        } else {
            echo "<h3>Page not found ❌</h3>";
        }

    }
}
?>