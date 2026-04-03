from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from extensions import db
from config import Config
from models import Produto, Cliente, Pedido, ItemPedido
from utils.pdf_generator import gerar_pdf_pedido
from datetime import datetime
from decimal import Decimal
import re

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# ── Helpers ──────────────────────────────────────────────────────────────────

def gerar_numero_pedido():
    ultimo = Pedido.query.order_by(Pedido.id.desc()).first()
    num = (ultimo.id + 1) if ultimo else 1
    return f'PED{num:05d}'


def stats_dashboard():
    total_produtos = Produto.query.filter_by(ativo=True).count()
    total_clientes = Cliente.query.filter_by(ativo=True).count()
    total_pedidos  = Pedido.query.count()
    pedidos_hoje   = Pedido.query.filter(
        db.func.date(Pedido.data) == datetime.utcnow().date()
    ).count()
    receita_total  = db.session.query(db.func.sum(Pedido.total)).scalar() or 0
    return dict(
        total_produtos=total_produtos,
        total_clientes=total_clientes,
        total_pedidos=total_pedidos,
        pedidos_hoje=pedidos_hoje,
        receita_total=float(receita_total),
    )


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    s = stats_dashboard()
    ultimos_pedidos = Pedido.query.order_by(Pedido.data.desc()).limit(8).all()
    return render_template('dashboard.html', ultimos_pedidos=ultimos_pedidos, **s)


# ══════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIAS = [
    'AMENDOIM', 'BALA', 'CHICLETE', 'PIRULITO',
    'CHOCOLATE', 'SALGADINHO', 'POTE', 'DIVERSOS',
]

@app.route('/produtos')
def produtos_lista():
    q          = request.args.get('q', '').strip()
    categoria  = request.args.get('categoria', '')
    page       = request.args.get('page', 1, type=int)

    query = Produto.query
    if q:
        query = query.filter(
            db.or_(
                Produto.nome.ilike(f'%{q}%'),
                Produto.codigo.ilike(f'%{q}%'),
            )
        )
    if categoria:
        query = query.filter(Produto.categoria == categoria)

    produtos = query.order_by(Produto.categoria, Produto.nome).paginate(page=page, per_page=30)
    return render_template('produtos/lista.html',
                           produtos=produtos, q=q,
                           categoria=categoria, categorias=CATEGORIAS)


@app.route('/produtos/novo', methods=['GET', 'POST'])
def produto_novo():
    if request.method == 'POST':
        codigo    = request.form['codigo'].strip().upper()
        nome      = request.form['nome'].strip().upper()
        categoria = request.form['categoria']
        preco     = request.form['preco'].replace(',', '.')
        unidade   = request.form.get('unidade', 'UN').upper()
        descricao = request.form.get('descricao', '').strip()

        if Produto.query.filter_by(codigo=codigo).first():
            flash('Código já cadastrado!', 'danger')
            return render_template('produtos/form.html', categorias=CATEGORIAS,
                                   form=request.form)

        p = Produto(codigo=codigo, nome=nome, categoria=categoria,
                    preco=Decimal(preco), unidade=unidade, descricao=descricao)
        db.session.add(p)
        db.session.commit()
        flash(f'Produto <strong>{nome}</strong> cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos_lista'))

    return render_template('produtos/form.html', categorias=CATEGORIAS, form={})


@app.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
def produto_editar(id):
    p = Produto.query.get_or_404(id)
    if request.method == 'POST':
        codigo_novo = request.form['codigo'].strip().upper()
        existe = Produto.query.filter(Produto.codigo == codigo_novo, Produto.id != id).first()
        if existe:
            flash('Código já usado por outro produto!', 'danger')
            return render_template('produtos/form.html', categorias=CATEGORIAS,
                                   form=request.form, produto=p)

        p.codigo    = codigo_novo
        p.nome      = request.form['nome'].strip().upper()
        p.categoria = request.form['categoria']
        p.preco     = Decimal(request.form['preco'].replace(',', '.'))
        p.unidade   = request.form.get('unidade', 'UN').upper()
        p.descricao = request.form.get('descricao', '').strip()
        p.ativo     = 'ativo' in request.form
        db.session.commit()
        flash('Produto atualizado!', 'success')
        return redirect(url_for('produtos_lista'))

    return render_template('produtos/form.html', categorias=CATEGORIAS,
                           form={}, produto=p)


@app.route('/produtos/<int:id>/excluir', methods=['POST'])
def produto_excluir(id):
    p = Produto.query.get_or_404(id)
    p.ativo = False
    db.session.commit()
    flash('Produto desativado!', 'warning')
    return redirect(url_for('produtos_lista'))


# ── API de busca de produtos (para o pedido) ─────────────────────────────────
@app.route('/api/produtos/buscar')
def api_buscar_produtos():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    resultados = Produto.query.filter(
        Produto.ativo == True,
        db.or_(
            Produto.nome.ilike(f'%{q}%'),
            Produto.codigo.ilike(f'%{q}%'),
        )
    ).order_by(Produto.nome).limit(20).all()
    return jsonify([p.to_dict() for p in resultados])


# ══════════════════════════════════════════════════════════════════════════════
# CLIENTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/clientes')
def clientes_lista():
    q    = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Cliente.query.filter_by(ativo=True)
    if q:
        query = query.filter(
            db.or_(
                Cliente.nome.ilike(f'%{q}%'),
                Cliente.cpf_cnpj.ilike(f'%{q}%'),
                Cliente.telefone.ilike(f'%{q}%'),
            )
        )
    clientes = query.order_by(Cliente.nome).paginate(page=page, per_page=20)
    return render_template('clientes/lista.html', clientes=clientes, q=q)


@app.route('/clientes/novo', methods=['GET', 'POST'])
def cliente_novo():
    if request.method == 'POST':
        c = Cliente(
            nome      = request.form['nome'].strip(),
            cpf_cnpj  = request.form.get('cpf_cnpj', '').strip(),
            telefone  = request.form.get('telefone', '').strip(),
            email     = request.form.get('email', '').strip(),
            endereco  = request.form.get('endereco', '').strip(),
            cidade    = request.form.get('cidade', '').strip(),
            estado    = request.form.get('estado', '').strip().upper(),
            observacoes = request.form.get('observacoes', '').strip(),
        )
        db.session.add(c)
        db.session.commit()
        flash(f'Cliente <strong>{c.nome}</strong> cadastrado!', 'success')
        return redirect(url_for('clientes_lista'))
    return render_template('clientes/form.html', cliente=None)


@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def cliente_editar(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        c.nome      = request.form['nome'].strip()
        c.cpf_cnpj  = request.form.get('cpf_cnpj', '').strip()
        c.telefone  = request.form.get('telefone', '').strip()
        c.email     = request.form.get('email', '').strip()
        c.endereco  = request.form.get('endereco', '').strip()
        c.cidade    = request.form.get('cidade', '').strip()
        c.estado    = request.form.get('estado', '').strip().upper()
        c.observacoes = request.form.get('observacoes', '').strip()
        db.session.commit()
        flash('Cliente atualizado!', 'success')
        return redirect(url_for('clientes_lista'))
    return render_template('clientes/form.html', cliente=c)


@app.route('/clientes/<int:id>/excluir', methods=['POST'])
def cliente_excluir(id):
    c = Cliente.query.get_or_404(id)
    c.ativo = False
    db.session.commit()
    flash('Cliente removido!', 'warning')
    return redirect(url_for('clientes_lista'))


@app.route('/api/clientes/buscar')
def api_buscar_clientes():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    resultado = Cliente.query.filter(
        Cliente.ativo == True,
        db.or_(
            Cliente.nome.ilike(f'%{q}%'),
            Cliente.cpf_cnpj.ilike(f'%{q}%'),
        )
    ).order_by(Cliente.nome).limit(15).all()
    return jsonify([c.to_dict() for c in resultado])


# ══════════════════════════════════════════════════════════════════════════════
# PEDIDOS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/pedidos')
def pedidos_lista():
    status = request.args.get('status', '')
    q      = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)

    query = Pedido.query.join(Cliente)
    if status:
        query = query.filter(Pedido.status == status)
    if q:
        query = query.filter(
            db.or_(
                Pedido.numero.ilike(f'%{q}%'),
                Cliente.nome.ilike(f'%{q}%'),
            )
        )
    pedidos = query.order_by(Pedido.data.desc()).paginate(page=page, per_page=20)
    return render_template('pedidos/lista.html', pedidos=pedidos, status=status, q=q)


@app.route('/pedidos/novo', methods=['GET', 'POST'])
def pedido_novo():
    if request.method == 'POST':
        data = request.get_json()

        cliente_id = data.get('cliente_id')
        itens_json = data.get('itens', [])
        desconto   = Decimal(str(data.get('desconto', '0')).replace(',', '.'))
        observacoes = data.get('observacoes', '')

        if not cliente_id:
            return jsonify({'ok': False, 'msg': 'Selecione um cliente!'})
        if not itens_json:
            return jsonify({'ok': False, 'msg': 'Adicione pelo menos um produto!'})

        pedido = Pedido(
            numero      = gerar_numero_pedido(),
            cliente_id  = cliente_id,
            desconto    = desconto,
            observacoes = observacoes,
            status      = 'pendente',
        )
        db.session.add(pedido)
        db.session.flush()

        for item in itens_json:
            prod = Produto.query.get(item['produto_id'])
            if not prod:
                continue
            qtd      = Decimal(str(item['quantidade']))
            preco    = Decimal(str(item['preco_unitario']))
            subtotal = round(qtd * preco, 2)
            ip = ItemPedido(
                pedido_id      = pedido.id,
                produto_id     = prod.id,
                quantidade     = qtd,
                preco_unitario = preco,
                subtotal       = subtotal,
            )
            db.session.add(ip)

        db.session.flush()
        pedido.calcular_total()
        db.session.commit()

        return jsonify({'ok': True, 'pedido_id': pedido.id, 'numero': pedido.numero})

    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return render_template('pedidos/novo.html', clientes=clientes)


@app.route('/pedidos/<int:id>')
def pedido_detalhe(id):
    pedido  = Pedido.query.get_or_404(id)
    cliente = pedido.cliente
    itens   = ItemPedido.query.filter_by(pedido_id=id).all()
    return render_template('pedidos/detalhe.html', pedido=pedido,
                           cliente=cliente, itens=itens)


@app.route('/pedidos/<int:id>/status', methods=['POST'])
def pedido_status(id):
    pedido = Pedido.query.get_or_404(id)
    novo   = request.form.get('status')
    if novo in ('pendente', 'confirmado', 'entregue', 'cancelado'):
        pedido.status = novo
        db.session.commit()
        flash('Status atualizado!', 'success')
    return redirect(url_for('pedido_detalhe', id=id))


@app.route('/pedidos/<int:id>/excluir', methods=['POST'])
def pedido_excluir(id):
    pedido = Pedido.query.get_or_404(id)
    db.session.delete(pedido)
    db.session.commit()
    flash('Pedido excluído!', 'warning')
    return redirect(url_for('pedidos_lista'))


@app.route('/pedidos/<int:id>/pdf')
def pedido_pdf(id):
    pedido  = Pedido.query.get_or_404(id)
    cliente = pedido.cliente
    itens   = ItemPedido.query.filter_by(pedido_id=id).all()
    buf = gerar_pdf_pedido(pedido, cliente, itens)
    nome_arquivo = f'Pedido_{pedido.numero}.pdf'
    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=nome_arquivo,
    )


# ══════════════════════════════════════════════════════════════════════════════
# INIT DB
# ══════════════════════════════════════════════════════════════════════════════

@app.cli.command('init-db')
def init_db():
    """Cria tabelas no banco de dados."""
    db.create_all()
    print('✅ Banco de dados criado com sucesso!')


@app.cli.command('seed-produtos')
def seed_produtos():
    """Insere produtos do catálogo JP Doces."""
    from seed_data import PRODUTOS_SEED
    inseridos = 0
    for p in PRODUTOS_SEED:
        if not Produto.query.filter_by(codigo=str(p['codigo'])).first():
            db.session.add(Produto(**p))
            inseridos += 1
    db.session.commit()
    print(f'✅ {inseridos} produtos inseridos!')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
