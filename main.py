# Получить APPLICATION_ID и APPLICATION_SECRET можно на сайте https://oauth.yandex.ru/

from disk import Disk
from time import sleep


if __name__ == '__main__':
    disk = None

    while True:
        if not disk:
            disk = Disk()
        if not disk.api:
            disk.get_assets()
        disk.recursive_upload()
        sleep(86400)
