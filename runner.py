import logging
logging.getLogger().setLevel(logging.DEBUG)

from taxii_server.http import app

def run_server():
    app.debug = True
    app.run(port=9000)


if __name__ == '__main__':
    run_server()
