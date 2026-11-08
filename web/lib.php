<?php
declare(strict_types=1);

function configuration(): array {
    static $config;
    if ($config === null) {
        $path = getenv('KIENZLE_CONFIG') ?: '/etc/kienzletranslate/config.json';
        $raw = @file_get_contents($path);
        if ($raw === false) { http_response_code(503); exit('kienzletranslate: Konfiguration fehlt.'); }
        $config = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
    }
    return $config;
}

function security_headers(): void {
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: no-referrer');
    header('X-Frame-Options: DENY');
    header("Permissions-Policy: microphone=(self), camera=(), geolocation=()");
}

function json_response(array $data, int $status = 200): never {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR);
    exit;
}

function api_error(string $message, int $status, string $code): never {
    json_response(['error' => $message, 'code' => $code], $status);
}

function session_identity(): ?string {
    $cookie = $_COOKIE['kt_session'] ?? '';
    $parts = explode('.', $cookie);
    if (count($parts) !== 3 || !preg_match('/^[a-f0-9]{32}$/D', $parts[0]) || !ctype_digit($parts[1])) return null;
    if ((int)$parts[1] < time() || (int)$parts[1] > time() + 31 * 86400) return null;
    $signature = hash_hmac('sha256', $parts[0].'.'.$parts[1], configuration()['session_secret']);
    return hash_equals($signature, $parts[2]) ? $parts[0] : null;
}

function csrf_token(string $sid): string {
    return hash_hmac('sha256', 'csrf:'.$sid, configuration()['session_secret']);
}

function set_auth_cookie(?string $sid): void {
    $expires = $sid === null ? time() - 3600 : time() + 30 * 86400;
    $value = $sid === null ? '' : $sid.'.'.$expires;
    if ($sid !== null) $value .= '.'.hash_hmac('sha256', $value, configuration()['session_secret']);
    setcookie('kt_session', $value, ['expires' => $expires, 'path' => '/', 'secure' => true,
        'httponly' => true, 'samesite' => 'Strict']);
}

function backend_request(string $method, string $path, ?string $body = null): array {
    $config = configuration();
    $curl = curl_init('http://127.0.0.1:'.(int)$config['model_port'].$path);
    curl_setopt_array($curl, [CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT => 20, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$config['backend_token'], 'Content-Type: audio/wav'],
        CURLOPT_PROXY => '', CURLOPT_PROTOCOLS => CURLPROTO_HTTP]);
    if ($body !== null) curl_setopt($curl, CURLOPT_POSTFIELDS, $body);
    $result = curl_exec($curl);
    $status = (int)curl_getinfo($curl, CURLINFO_HTTP_CODE);
    $type = curl_getinfo($curl, CURLINFO_CONTENT_TYPE) ?: 'application/json';
    if ($result === false || $status === 0) return [503, 'application/json', '{"error":"Modellservice ist nicht erreichbar.","code":"backend_unavailable"}'];
    return [$status, $type, $result];
}

function forward_backend(string $method, string $path, ?string $body = null): never {
    [$status, $type, $result] = backend_request($method, $path, $body);
    http_response_code($status);
    header('Content-Type: '.(str_starts_with($type, 'audio/wav') ? 'audio/wav' : 'application/json; charset=utf-8'));
    echo $result;
    exit;
}
