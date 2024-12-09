<?php
// Path to your Bash script
$scriptPath = 'webhook-handler.sh';

// Execute the Bash script and capture the output
$output = shell_exec("bash $scriptPath 2>&1");

// Save the output to a log file
$logFile = '../api-update-log.txt';
file_put_contents($logFile, $output, FILE_APPEND); // Use FILE_APPEND to add new output without overwriting

// Display the output (optional)
echo "<pre>$output</pre>";
?>