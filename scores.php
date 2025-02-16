<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

$scoresFile = __DIR__ . '/scores.json';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (file_exists($scoresFile)) {
        echo file_get_contents($scoresFile);
    } else {
        // Создаем файл с начальными данными, если его нет
        $initialData = [
            'evenTotalScore' => 0,
            'oddTotalScore' => 0,
            'evenIPs' => [],
            'oddIPs' => []
        ];
        file_put_contents($scoresFile, json_encode($initialData));
        echo json_encode($initialData);
    }
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if ($data === null) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON data']);
        exit;
    }

    // Проверяем, что все необходимые поля присутствуют
    $requiredFields = ['evenTotalScore', 'oddTotalScore', 'evenIPs', 'oddIPs'];
    foreach ($requiredFields as $field) {
        if (!isset($data[$field])) {
            http_response_code(400);
            echo json_encode(['error' => "Missing required field: $field"]);
            exit;
        }
    }

    // Сохраняем данные
    if (file_put_contents($scoresFile, json_encode($data)) === false) {
        http_response_code(500);
        echo json_encode(['error' => 'Failed to save data']);
        exit;
    }

    echo json_encode(['status' => 'success']);
} else {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
}
?>
