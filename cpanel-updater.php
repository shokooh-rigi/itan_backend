<?php
// Path to your Bash script
$scriptPath = 'webhook-handler.sh';

// Run the script in the background
// "&" ensures the script runs in the background
// ">>" appends output to the log file
// "2>&1" redirects errors to the log file
exec("bash $scriptPath &");

// Respond to GitHub webhook immediately
http_response_code(200);
echo "OK";
?>
