from .auth import auth_bp
from .dashboard import dashboard_bp
from .obras import obras_bp
from .instalacoes import instalacoes_bp
from .usuario import usuarios_bp
from .clientes import clientes_bp
from .contratos import contratos_bp
from .catalogo import catalogo_bp
from .cad_contratos import cad_contratos_bp

def init_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(obras_bp, url_prefix='/obras')
    app.register_blueprint(instalacoes_bp, url_prefix='/instalacoes')
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(contratos_bp)
    app.register_blueprint(catalogo_bp)
    app.register_blueprint(cad_contratos_bp)

    

    