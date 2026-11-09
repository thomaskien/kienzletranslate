<?php
declare(strict_types=1);
require __DIR__.'/lib.php';
security_headers();
$config = configuration();
$lang = ($_GET['lang'] ?? $config['language'] ?? 'de') === 'en' ? 'en' : 'de';
$en = $lang === 'en';
$word = $en ? 'ACCEPT' : 'AKZEPTIEREN';
$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (($_POST['confirmation'] ?? '') !== $word) {
        $error = $en ? 'Please enter ACCEPT exactly.' : 'Bitte genau AKZEPTIEREN eingeben.';
    } else {
        $cert = @file_get_contents($config['ca_public_path']);
        if ($cert === false) { http_response_code(503); exit('CA certificate unavailable'); }
        header('Content-Type: application/x-x509-ca-cert');
        header('Content-Disposition: attachment; filename="kienzletranslate-root-ca.cer"');
        echo $cert;
        exit;
    }
}
function e(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }
$url = $config['public_url'];
?><!doctype html>
<html lang="<?= $lang ?>"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>kienzletranslate · <?= $en ? 'Setup' : 'Einrichtung' ?></title>
<style>body{margin:0;background:#0b0e0c;color:#f5f7f5;font:17px/1.55 system-ui,sans-serif}main{max-width:720px;padding:32px 24px 60px;margin:auto}nav{display:flex;justify-content:space-between;gap:15px}a{color:#8bed9b}h1{font-size:36px;line-height:1.15;margin-top:45px}section{padding:22px;border:1px solid #3d4d42;border-radius:18px;margin:24px 0}.license{border-color:#e5c461;background:#272416}input,button{box-sizing:border-box;border-radius:10px;padding:13px;font:inherit;max-width:100%}input{background:#131a15;color:white;border:1px solid #91a796;width:100%;margin:10px 0}button{background:#85ef9c;border:0;color:#07160b;font-weight:650;cursor:pointer}.error{color:#ffb5af}code{overflow-wrap:anywhere;font-size:13px}.muted{color:#bdc8c0}</style>
<main><nav><strong>kienzletranslate</strong><span><a href="?lang=de">Deutsch</a> · <a href="?lang=en">English</a></span></nav>
<h1><?= $en ? 'Set up your iPad' : 'iPad einrichten' ?></h1>
<p><?= $en ? 'Install the local certificate once, then open the app securely over HTTPS.' : 'Einmal das lokale Zertifikat installieren, anschließend die App sicher über HTTPS öffnen.' ?></p>
<section class="license"><h2><?= $en ? 'Model licence — noncommercial use only' : 'Modelllizenz — nur nichtkommerzielle Nutzung' ?></h2>
<p><?= $en ? 'This application uses Meta SeamlessM4T v2 Large. Its model weights are licensed under CC BY-NC 4.0. Commercial use is not permitted under this licence. Attribution and the other licence terms apply. The application source code has a separate MIT licence.' : 'Diese Anwendung verwendet Meta SeamlessM4T v2 Large. Die Modellgewichte stehen unter CC BY-NC 4.0. Kommerzielle Nutzung ist unter dieser Lizenz nicht gestattet. Namensnennung und die weiteren Lizenzbedingungen sind einzuhalten. Der Anwendungscode hat eine separate MIT-Lizenz.' ?></p>
<p><a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener"><?= $en ? 'Read the licence' : 'Lizenz lesen' ?></a> · <a href="https://huggingface.co/facebook/seamless-m4t-v2-large" target="_blank" rel="noopener">Meta SeamlessM4T v2 Large</a></p>
<p><?= $en ? 'Technical prototype. No medical validation. Use test data.' : 'Technischer Prototyp ohne medizinische Validierung. Testdaten verwenden.' ?></p>
<form method="post"><label for="confirmation"><?= $en ? 'I have read and accept the model licence. Type ACCEPT to confirm:' : 'Ich habe die Modelllizenz gelesen und akzeptiere sie. Zur Bestätigung AKZEPTIEREN eingeben:' ?></label>
<input id="confirmation" name="confirmation" autocomplete="off" autocapitalize="characters" spellcheck="false" required pattern="<?= $word ?>" placeholder="<?= $word ?>">
<?php if ($error): ?><p class="error"><?= e($error) ?></p><?php endif ?>
<button type="submit"><?= $en ? 'Accept and download CA certificate' : 'Bestätigen und CA-Zertifikat laden' ?></button></form></section>
<section><h2><?= $en ? 'Next steps on the iPad' : 'Danach auf dem iPad' ?></h2>
<ol><li><?= $en ? 'Settings → Profile Downloaded → Install.' : 'Einstellungen → Profil geladen → Installieren.' ?></li>
<li><?= $en ? 'Settings → General → About → Certificate Trust Settings: enable full trust for kienzletranslate Local CA.' : 'Einstellungen → Allgemein → Info → Zertifikatsvertrauenseinstellungen: volles Vertrauen für kienzletranslate Local CA aktivieren.' ?></li>
<li><a href="<?= e($url) ?>"><?= e($url) ?></a> <?= password_required() ? ($en ? 'open and sign in with the installation password.' : 'öffnen und mit dem Zugangspasswort anmelden.') : ($en ? 'open — no password required.' : 'öffnen — kein Passwort erforderlich.') ?></li>
<li><?= $en ? 'Safari → Share → Add to Home Screen.' : 'Safari → Teilen → Zum Home-Bildschirm.' ?></li></ol>
<p class="muted"><?= $en ? 'Verify the SHA-256 fingerprint against the installer output before trusting this CA. HTTP does not authenticate the certificate download.' : 'Vor dem Vertrauen den SHA-256-Fingerabdruck mit der Ausgabe des Installers vergleichen. HTTP schützt den Zertifikatsdownload nicht vor Austausch.' ?></p>
<code><?= e($config['ca_fingerprint'] ?? '') ?></code></section>
</main></html>
