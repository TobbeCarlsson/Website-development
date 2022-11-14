
from flask_server import app
from werkzeug.middleware.proxy_fix import ProxyFix

if __name__ == '__main__':
    # This is without the proxy fix (see https://flask.palletsprojects.com/en/2.1.x/deploying/proxy_fix/)
    app.run(debug=True, threaded = True)
    # This is with it:
    # app.wsgi_app = ProxyFix(app.wsgi_app, x_for = 1, x_proto = 1, x_host = 1, x_prefix = 1)
