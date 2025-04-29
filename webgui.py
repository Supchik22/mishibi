import webview
import os

# Отримуємо абсолютний шлях до index.html
html_file = os.path.abspath('main.html')
file_url = f'file://{html_file}'

# Створюємо вікно з локальним HTML
webview.create_window('Chat Mishibi', file_url)
webview.start()
