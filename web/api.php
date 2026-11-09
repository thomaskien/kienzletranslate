<?php
declare(strict_types=1);
require __DIR__.'/lib.php';
security_headers();
$config = configuration();
if (($_SERVER['HTTPS'] ?? '') !== 'on') api_error('HTTPS ist erforderlich.', 400, 'https_required');
$route = trim((string)($_GET['route'] ?? ''), '/');
$method = $_SERVER['REQUEST_METHOD'];
$sid = session_identity();

if ($method !== 'GET') {
    if (($_SERVER['HTTP_SEC_FETCH_SITE'] ?? '') === 'cross-site') api_error('Zugriff abgewiesen.', 403, 'origin');
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';
    if ($origin !== '' && $origin !== 'https://'.($_SERVER['HTTP_HOST'] ?? '')) api_error('Zugriff abgewiesen.', 403, 'origin');
}

if ($route === 'login' && $method === 'POST') {
    if (!password_required()) api_error('Passwortschutz ist deaktiviert.', 409, 'password_disabled');
    $body = file_get_contents('php://input', false, null, 0, 4097);
    if (strlen($body) > 4096) api_error('Eingabe zu lang.', 413, 'size');
    $input = json_decode($body, true);
    $password = is_array($input) && is_string($input['password'] ?? null) ? $input['password'] : '';
    if (strlen($password) > 1024 || !password_verify($password, $config['password_hash'] ?? '')) {
        usleep(300000);
        api_error('Zugangspasswort stimmt nicht.', 401, 'login_failed');
    }
    set_auth_cookie(bin2hex(random_bytes(16)), true);
    json_response(['ok' => true]);
}

if ($route === 'bootstrap' && $method === 'GET') {
    if ($sid === null && !password_required()) {
        $sid = bin2hex(random_bytes(16));
        set_auth_cookie($sid);
    }
    if ($sid === null) json_response(['authenticated' => false, 'password_required' => true, 'version' => $config['version'] ?? '1.6.1']);
    [$status, , $health] = backend_request('GET', '/health');
    json_response(['authenticated' => true, 'password_required' => password_required(), 'csrf' => csrf_token($sid), 'session_id' => $sid,
        'languages' => json_decode(file_get_contents(dirname(__DIR__).'/backend/languages.json'), true),
        'model' => $status === 200 ? json_decode($health, true) : ['state' => 'error', 'error' => 'Modellservice nicht erreichbar.'],
        'version' => $config['version'] ?? '1.6.1']);
}

if ($sid === null) api_error(password_required() ? 'Bitte anmelden.' : 'Bitte App neu laden.', 401, 'authentication_required');
if ($method !== 'GET' && !hash_equals(csrf_token($sid), $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '')) api_error('Sitzung bitte neu laden.', 403, 'csrf');

if ($route === 'logout' && $method === 'POST') {
    backend_request('DELETE', '/sessions/'.$sid);
    set_auth_cookie(null);
    json_response(['ok' => true]);
}
if ($route === 'session' && $method === 'DELETE') forward_backend('DELETE', '/sessions/'.$sid);
if ($route === 'heartbeat' && $method === 'POST') {
    $body = file_get_contents('php://input', false, null, 0, 1025);
    if (strlen($body) > 1024) api_error('Eingabe zu groß.', 413, 'size');
    forward_backend('POST', '/sessions/'.$sid.'/heartbeat', $body, 'application/json');
}
if ($route === 'health' && $method === 'GET') forward_backend('GET', '/health');
if (in_array($route, ['model/load', 'model/unload'], true) && $method === 'POST') forward_backend('POST', '/'.$route);
if ($route === 'utterances' && $method === 'POST') {
    $params = [];
    foreach (['utterance_id', 'speaker_side', 'source_lang', 'target_lang', 'tts', 'generation'] as $key) {
        if (!isset($_GET[$key]) || !is_string($_GET[$key]) || strlen($_GET[$key]) > 80) api_error('Ungültige Aufnahmedaten.', 400, 'metadata');
        $params[$key] = $_GET[$key];
    }
    if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 16777216) api_error('Aufnahme zu groß.', 413, 'size');
    $body = file_get_contents('php://input', false, null, 0, 16777217);
    if (strlen($body) > 16777216) api_error('Aufnahme zu groß.', 413, 'size');
    forward_backend('POST', '/sessions/'.$sid.'/utterances?'.http_build_query($params), $body);
}
if ($method === 'GET' && preg_match('~^(utterances|audio)/([a-fA-F0-9-]{36})$~D', $route)) {
    forward_backend('GET', '/sessions/'.$sid.'/'.$route);
}
api_error('Nicht gefunden.', 404, 'not_found');
