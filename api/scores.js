// Используем простое JSON-хранилище
const fs = require('fs');
const path = require('path');

const SCORES_FILE = path.join(process.cwd(), 'data', 'scores.json');

// Убеждаемся, что директория существует
if (!fs.existsSync(path.dirname(SCORES_FILE))) {
    fs.mkdirSync(path.dirname(SCORES_FILE), { recursive: true });
}

// Создаем файл с начальными данными, если его нет
if (!fs.existsSync(SCORES_FILE)) {
    fs.writeFileSync(SCORES_FILE, JSON.stringify({
        evenTotalScore: 0,
        oddTotalScore: 0,
        evenIPs: [],
        oddIPs: []
    }));
}

module.exports = async (req, res) => {
    // Разрешаем CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }

    try {
        if (req.method === 'GET') {
            // Читаем текущие данные
            const data = JSON.parse(fs.readFileSync(SCORES_FILE, 'utf8'));
            return res.json(data);
        }
        
        if (req.method === 'POST') {
            // Обновляем данные
            const data = req.body;
            fs.writeFileSync(SCORES_FILE, JSON.stringify(data, null, 2));
            return res.json({ success: true });
        }
    } catch (error) {
        console.error('Error:', error);
        return res.status(500).json({ error: error.message });
    }
};
