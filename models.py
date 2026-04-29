from datetime import datetime
from extensions import db


class Produto(db.Model):
    __tablename__ = 'produtos'
    id          = db.Column(db.Integer, primary_key=True)
    codigo      = db.Column(db.String(20), unique=True, nullable=False)
    nome        = db.Column(db.String(120), nullable=False)
    categoria   = db.Column(db.String(50), nullable=False)
    descricao   = db.Column(db.Text)
    preco       = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    preco_compra = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    unidade     = db.Column(db.String(20), default='UN')
    ativo       = db.Column(db.Boolean, default=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    itens = db.relationship('ItemPedido', backref='produto', lazy=True)

    def to_dict(self):
        return {
            'id':        self.id,
            'codigo':    self.codigo,
            'nome':      self.nome,
            'categoria': self.categoria,
            'descricao': self.descricao or '',
            'preco':     float(self.preco),
            'unidade':   self.unidade,
            'ativo':     self.ativo,
        }

    def __repr__(self):
        return f'<Produto {self.codigo} - {self.nome}>'


class Cliente(db.Model):
    __tablename__ = 'clientes'
    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(120), nullable=False)
    cpf_cnpj    = db.Column(db.String(20))
    telefone    = db.Column(db.String(20))
    email       = db.Column(db.String(100))
    endereco    = db.Column(db.String(200))
    cidade      = db.Column(db.String(80))
    estado      = db.Column(db.String(2))
    observacoes = db.Column(db.Text)
    ativo       = db.Column(db.Boolean, default=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'id':       self.id,
            'nome':     self.nome,
            'cpf_cnpj': self.cpf_cnpj or '',
            'telefone': self.telefone or '',
            'email':    self.email or '',
            'cidade':   self.cidade or '',
            'estado':   self.estado or '',
        }

    def __repr__(self):
        return f'<Cliente {self.nome}>'


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id          = db.Column(db.Integer, primary_key=True)
    numero      = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id  = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    data        = db.Column(db.DateTime, default=datetime.utcnow)
    status      = db.Column(db.String(20), default='pendente')   # pendente | confirmado | entregue | cancelado
    total       = db.Column(db.Numeric(10, 2), default=0)
    desconto    = db.Column(db.Numeric(10, 2), default=0)
    observacoes = db.Column(db.Text)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    itens = db.relationship('ItemPedido', backref='pedido', lazy=True, cascade='all, delete-orphan')

    def calcular_total(self):
        total = sum(float(i.subtotal) for i in self.itens)
        self.total = round(total - float(self.desconto or 0), 2)
        return self.total

    def __repr__(self):
        return f'<Pedido {self.numero}>'


class ItemPedido(db.Model):
    __tablename__ = 'itens_pedido'
    id              = db.Column(db.Integer, primary_key=True)
    pedido_id       = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    produto_id      = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    quantidade      = db.Column(db.Numeric(10, 3), nullable=False)
    preco_unitario  = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal        = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<ItemPedido pedido={self.pedido_id} produto={self.produto_id}>'
