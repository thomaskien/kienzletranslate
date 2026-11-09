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

function password_required(): bool {
    $config = configuration();
    // Retain an older installation's explicit password until it is switched off.
    return (bool)($config['password_required'] ?? isset($config['password_hash']));
}

function session_identity(): ?string {
    $cookie = $_COOKIE['kt_session'] ?? '';
    $parts = explode('.', $cookie);
    if (count($parts) !== 4 || !preg_match('/^[a-f0-9]{32}$/D', $parts[0]) || !ctype_digit($parts[1])) return null;
    if ((int)$parts[1] < time() || (int)$parts[1] > time() + 31 * 86400) return null;
    if (!in_array($parts[2], ['open', 'password'], true)) return null;
    if (password_required() && $parts[2] !== 'password') return null;
    $signature = hash_hmac('sha256', implode('.', array_slice($parts, 0, 3)), configuration()['session_secret']);
    return hash_equals($signature, $parts[3]) ? $parts[0] : null;
}

function csrf_token(string $sid): string {
    return hash_hmac('sha256', 'csrf:'.$sid, configuration()['session_secret']);
}

function session_cookie_value(string $sid, bool $password_authenticated): string {
    $value = $sid.'.'.(time() + 30 * 86400).'.'.($password_authenticated ? 'password' : 'open');
    return $value.'.'.hash_hmac('sha256', $value, configuration()['session_secret']);
}

function set_auth_cookie(?string $sid, bool $password_authenticated = false): void {
    $expires = $sid === null ? time() - 3600 : time() + 30 * 86400;
    $value = $sid === null ? '' : session_cookie_value($sid, $password_authenticated);
    setcookie('kt_session', $value, ['expires' => $expires, 'path' => '/', 'secure' => true,
        'httponly' => true, 'samesite' => 'Strict']);
}

function backend_request(string $method, string $path, ?string $body = null, string $contentType = 'audio/wav'): array {
    $config = configuration();
    $curl = curl_init('http://127.0.0.1:'.(int)$config['model_port'].$path);
    curl_setopt_array($curl, [CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true,
        CURLOPT_CONNECTTIMEOUT => 3, CURLOPT_TIMEOUT => 20, CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_HTTPHEADER => ['Authorization: Bearer '.$config['backend_token'], 'Content-Type: '.$contentType],
        CURLOPT_PROXY => '', CURLOPT_PROTOCOLS => CURLPROTO_HTTP]);
    if ($body !== null) curl_setopt($curl, CURLOPT_POSTFIELDS, $body);
    $result = curl_exec($curl);
    $status = (int)curl_getinfo($curl, CURLINFO_HTTP_CODE);
    $type = curl_getinfo($curl, CURLINFO_CONTENT_TYPE) ?: 'application/json';
    if ($result === false || $status === 0) return [503, 'application/json', '{"error":"Modellservice ist nicht erreichbar.","code":"backend_unavailable"}'];
    return [$status, $type, $result];
}

function forward_backend(string $method, string $path, ?string $body = null, string $contentType = 'audio/wav'): never {
    [$status, $type, $result] = backend_request($method, $path, $body, $contentType);
    http_response_code($status);
    header('Content-Type: '.(str_starts_with($type, 'audio/wav') ? 'audio/wav' : 'application/json; charset=utf-8'));
    echo $result;
    exit;
}
