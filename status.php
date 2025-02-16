<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$status = [
    'php_running' => true,
    'file_permissions' => is_writable('.') && is_writable('./scores.txt'),
    'json_support' => function_exists('json_encode'),
    'version' => PHP_VERSION
];

echo json_encode($status);
