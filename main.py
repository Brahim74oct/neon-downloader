import os
import threading
from urllib.parse import urlparse

import yt_dlp
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder

KV = """
BoxLayout:
    orientation: "vertical"
    padding: "22dp"
    spacing: "14dp"

    canvas.before:
        Color:
            rgba: (0.025, 0.04, 0.10, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "[b]NEON[/b] [color=#00F5D4]DOWNLOADER[/color]"
        markup: True
        font_size: "27sp"
        size_hint_y: None
        height: "65dp"

    Label:
        text: "YouTube • Facebook • Instagram • TikTok"
        font_size: "13sp"
        color: (0.65, 0.75, 0.88, 1)
        size_hint_y: None
        height: "35dp"

    TextInput:
        id: url
        hint_text: "Colle le lien de la vidéo ici"
        multiline: False
        size_hint_y: None
        height: "54dp"
        padding: "12dp"
        background_color: (0.09, 0.12, 0.21, 1)
        foreground_color: (1, 1, 1, 1)
        cursor_color: (0, 0.96, 0.83, 1)

    Button:
        text: "TÉLÉCHARGER LA VIDÉO"
        size_hint_y: None
        height: "54dp"
        background_normal: ""
        background_color: (0, 0.85, 0.70, 1)
        color: (0.02, 0.05, 0.1, 1)
        on_release: app.start_download("video")

    Button:
        text: "TÉLÉCHARGER L'AUDIO"
        size_hint_y: None
        height: "54dp"
        background_normal: ""
        background_color: (0.40, 0.30, 0.95, 1)
        on_release: app.start_download("audio")

    ProgressBar:
        id: progress
        max: 100
        value: 0
        size_hint_y: None
        height: "12dp"

    Label:
        id: percent
        text: "0 %"
        size_hint_y: None
        height: "28dp"

    Label:
        id: status
        text: "Prêt à télécharger"
        halign: "center"
        valign: "middle"
        text_size: self.width, None

    Label:
        text: "Les fichiers sont enregistrés dans le dossier de l'application."
        font_size: "11sp"
        color: (0.60, 0.67, 0.78, 1)
        size_hint_y: None
        height: "40dp"
"""

class NeonDownloader(App):
    busy = False

    def build(self):
        self.title = "Neon Downloader"
        return Builder.load_string(KV)

    def status(self, message):
        self.root.ids.status.text = message

    def set_progress(self, value):
        value = max(0, min(100, value))
        self.root.ids.progress.value = value
        self.root.ids.percent.text = f"{int(value)} %"

    def start_download(self, mode):
        if self.busy:
            self.status("Un téléchargement est déjà en cours.")
            return

        url = self.root.ids.url.text.strip()
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            self.status("Colle un lien HTTP ou HTTPS valide.")
            return

        self.busy = True
        self.set_progress(0)
        self.status("Connexion au site…")

        threading.Thread(
            target=self.download,
            args=(url, mode),
            daemon=True
        ).start()

    def download(self, url, mode):
        try:
            folder = os.path.join(self.user_data_dir, "Downloads")
            os.makedirs(folder, exist_ok=True)

            def hook(data):
                if data.get("status") == "downloading":
                    total = (
                        data.get("total_bytes")
                        or data.get("total_bytes_estimate")
                    )
                    current = data.get("downloaded_bytes", 0)

                    if total:
                        pct = current * 100 / total
                        Clock.schedule_once(
                            lambda dt, p=pct: self.set_progress(p)
                        )

                    speed = data.get("speed")
                    if speed:
                        message = f"Téléchargement… {speed / 1024:.0f} Ko/s"
                        Clock.schedule_once(
                            lambda dt, m=message: self.status(m)
                        )

            options = {
                "outtmpl": os.path.join(folder, "%(title).100s.%(ext)s"),
                "noplaylist": True,
                "progress_hooks": [hook],
                "quiet": True,
                "retries": 3,
            }

            if mode == "video":
                options["format"] = "best[ext=mp4]/best"
            else:
                # Télécharge l'audio dans son format d'origine.
                # La conversion MP3 nécessite FFmpeg intégré à l'APK.
                options["format"] = "bestaudio/best"

            with yt_dlp.YoutubeDL(options) as downloader:
                downloader.download([url])

            Clock.schedule_once(lambda dt: self.set_progress(100))
            Clock.schedule_once(
                lambda dt: self.status(
                    "Téléchargement terminé ! Consulte le dossier de l'application."
                )
            )

        except Exception as error:
            message = str(error).replace("\n", " ")[:220]
            Clock.schedule_once(
                lambda dt, m=message: self.status("Erreur : " + m)
            )

        finally:
            Clock.schedule_once(lambda dt: setattr(self, "busy", False))


if __name__ == "__main__":
    NeonDownloader().run()
