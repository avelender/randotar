<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST');
header('Access-Control-Allow-Headers: Content-Type');

$scoresFile = 'scores.txt';

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (file_exists($scoresFile)) {
        $content = file_get_contents($scoresFile);
        $scores = [];
        
        // Парсим данные из текстового файла
        foreach(explode("\n", $content) as $line) {
            if (strpos($line, ':') !== false) {
                list($key, $value) = explode(':', $line, 2);
                $scores[trim($key)] = trim($value);
            }
        }
        
        // Преобразуем в нужный формат
        $data = [
            'evenTotalScore' => intval($scores['evenTotalScore'] ?? 0),
            'oddTotalScore' => intval($scores['oddTotalScore'] ?? 0),
            'evenIPs' => array_filter(explode(',', $scores['evenIPs'] ?? '')),
            'oddIPs' => array_filter(explode(',', $scores['oddIPs'] ?? ''))
        ];
        
        echo json_encode($data);
    } else {
        echo json_encode([
            'evenTotalScore' => 0,
            'oddTotalScore' => 0,
            'evenIPs' => [],
            'oddIPs' => []
        ]);
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

    // Форматируем данные для сохранения
    $content = "evenTotalScore: " . ($data['evenTotalScore'] ?? 0) . "\n" .
               "oddTotalScore: " . ($data['oddTotalScore'] ?? 0) . "\n" .
               "evenIPs: " . implode(',', $data['evenIPs'] ?? []) . "\n" .
               "oddIPs: " . implode(',', $data['oddIPs'] ?? []);
    
    if (file_put_contents($scoresFile, $content) === false) {
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
