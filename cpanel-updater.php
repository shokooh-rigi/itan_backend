<?php
// Path to your Bash script
$scriptPath = 'webhook-handler.sh';

// Execute the Bash script
$output = shell_exec("bash $scriptPath 2>&1");

// Display or log the output (for debugging)
echo "<pre>$output</pre>";
?>