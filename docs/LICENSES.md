# Lizenzen / Licences

- **Anwendung / application:** MIT, siehe `LICENSE`.
- **Modell / model:** Meta / Facebook AI, `facebook/seamless-m4t-v2-large`,
  [offizielle Modellbeschreibung](https://huggingface.co/facebook/seamless-m4t-v2-large).
  Modellgewichte: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
  Nichtkommerzielle Nutzung, Namensnennung und weitere Lizenzbedingungen beachten.
  Die Bestätigung erweitert die Rechte der Lizenz nicht.
- **Checkpoint:** `5f8cc790b19fc3f67a61c105133b20b34e3dcb76`.
  Gewichte werden bei der Installation separat heruntergeladen, nicht im Git-Repo
  oder in Anwendungs-Releases verteilt. Die Modell-README wird mit heruntergeladen.
- **Modellimplementierung:** Hugging Face Transformers / Meta Seamless. Die
  Lizenzen der verwendeten Bibliotheken gelten zusätzlich; siehe jeweilige Pakete.

The application licence does not override the model licence. Commercial use of
the model weights is not permitted under CC BY-NC 4.0. No medical validation is
claimed. The initial release is a technical prototype for noncommercial use with
test data.

Installer acknowledgement (German):
> Ich habe die Modelllizenz gelesen und akzeptiere sie. AKZEPTIEREN

Installer acknowledgement (English):
> I have read and accept the model licence. ACCEPT

## CPU-Spracherkennung ab v1.6

Whisper base (`Systran/faster-whisper-base`, Revision
`ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`) wird separat unter MIT-Lizenz
installiert. Die nichtkommerzielle Beschränkung des Seamless-Modells bleibt
unverändert. faster-whisper und die darin enthaltene Silero-VAD sind zusätzliche
CPU-Komponenten; Paketlizenzdateien bleiben in ihrem separaten venv erhalten.
