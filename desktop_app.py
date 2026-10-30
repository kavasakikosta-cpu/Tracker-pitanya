# -*- coding: utf-8 -*-
"""Настольная версия (Windows .exe): открывает приложение в отдельном окне.
Данные (план, дневник, аллергии) сохраняются между запусками:
 - сервер всегда стартует на одном и том же порту (иначе браузерное хранилище «теряется»);
 - хранилище окна лежит в постоянной папке пользователя."""
import os, sys, threading, webbrowser, http.server, socketserver, functools

PORTS = (48151, 48152, 48153)


def base():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def data_dir():
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    p = os.path.join(root, "TrekerPitaniya")
    os.makedirs(p, exist_ok=True)
    return p


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def start_server(www):
    handler = functools.partial(Quiet, directory=www)
    socketserver.TCPServer.allow_reuse_address = True
    for port in PORTS:
        try:
            srv = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
        except OSError:
            continue
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        return srv, port
    raise RuntimeError("Не удалось занять порт для локального сервера")


def main():
    srv, port = start_server(os.path.join(base(), "www"))
    url = f"http://127.0.0.1:{port}/index.html"
    try:
        import webview  # pywebview
        webview.create_window("Трекер питания", url, width=430, height=860, min_size=(360, 600))
        webview.start(private_mode=False, storage_path=os.path.join(data_dir(), "webview"))
    except Exception:
        webbrowser.open(url)
        print(f"Трекер питания открыт в браузере: {url}\nНе закрывайте это окно, пока пользуетесь приложением.")
        threading.Event().wait()
    srv.shutdown()


if __name__ == "__main__":
    main()
