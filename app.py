from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
from extensions import db
from config import Config
from models import Produto, Cliente, Pedido, ItemPedido, Boleto
from utils.pdf_generator import gerar_pdf_pedido
from datetime import datetime, date, timedelta, time
from calendar import monthrange
from decimal import Decimal
from werkzeug.utils import secure_filename
import re
import os
import uuid

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
    receita_total = db.session.query(db.func.sum(Pedido.total)).scalar() or 0
    custo_total = db.session.query(
        db.func.sum(ItemPedido.quantidade * db.func.coalesce(Produto.preco_compra, 0))
    ).join(Produto, Produto.id == ItemPedido.produto_id).scalar() or 0
    lucro_total = Decimal(str(receita_total)) - Decimal(str(custo_total))
    return dict(
        total_produtos=total_produtos,
        total_clientes=total_clientes,
        total_pedidos=total_pedidos,
        pedidos_hoje=pedidos_hoje,
        receita_total=float(receita_total),
        custo_total=float(custo_total),
        lucro_total=float(lucro_total),
    )


def listar_opcoes_meses(qtd=12):
    hoje = date.today().replace(day=1)
    nomes_meses = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    meses = []
    atual = hoje

    for _ in range(qtd):
        meses.append({
            'valor': atual.strftime('%Y-%m'),
            'label': f"{nomes_meses[atual.month - 1]}/{atual.year}",
        })
        if atual.month == 1:
            atual = atual.replace(year=atual.year - 1, month=12)
        else:
            atual = atual.replace(month=atual.month - 1)

    return meses


def resolver_periodo_relatorio(periodo, data_inicio_str='', data_fim_str='', mes_ref=''):
    hoje = date.today()

    if periodo == 'hoje':
        data_inicio = hoje
        data_fim = hoje
    elif periodo == 'semana':
        data_inicio = hoje - timedelta(days=hoje.weekday())
        data_fim = hoje
    elif periodo == 'mes':
        try:
            if mes_ref:
                referencia = datetime.strptime(mes_ref, '%Y-%m').date()
            else:
                referencia = hoje.replace(day=1)
        except ValueError:
            referencia = hoje.replace(day=1)

        ultimo_dia = monthrange(referencia.year, referencia.month)[1]
        data_inicio = referencia.replace(day=1)
        data_fim = referencia.replace(day=ultimo_dia)
    elif periodo == 'personalizado' and data_inicio_str and data_fim_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').date()
        except ValueError:
            ultimo_dia = monthrange(hoje.year, hoje.month)[1]
            data_inicio = hoje.replace(day=1)
            data_fim = hoje.replace(day=ultimo_dia)
            periodo = 'mes'
    else:
        ultimo_dia = monthrange(hoje.year, hoje.month)[1]
        data_inicio = hoje.replace(day=1)
        data_fim = hoje.replace(day=ultimo_dia)
        periodo = 'mes'

    if data_inicio > data_fim:
        data_inicio, data_fim = data_fim, data_inicio

    inicio_dt = datetime.combine(data_inicio, time.min)
    fim_dt = datetime.combine(data_fim, time.max)
    return periodo, data_inicio, data_fim, inicio_dt, fim_dt


# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    s = stats_dashboard()
    ultimos_pedidos = Pedido.query.order_by(Pedido.data.desc()).limit(8).all()
    return render_template('dashboard.html', ultimos_pedidos=ultimos_pedidos, **s)


@app.route('/relatorios')
def relatorios():
    periodo = request.args.get('periodo', 'mes')
    data_inicio_str = request.args.get('data_inicio', '')
    data_fim_str = request.args.get('data_fim', '')
    mes_ref = request.args.get('mes_ref', '')

    periodo, data_inicio, data_fim, inicio_dt, fim_dt = resolver_periodo_relatorio(
        periodo, data_inicio_str, data_fim_str, mes_ref
    )
    opcoes_meses = listar_opcoes_meses()
    if not mes_ref:
        mes_ref = data_inicio.strftime('%Y-%m')

    pedidos_base = Pedido.query.filter(Pedido.data >= inicio_dt, Pedido.data <= fim_dt)

    total_pedidos = pedidos_base.count()
    total_vendas = pedidos_base.with_entities(db.func.sum(Pedido.total)).scalar() or 0
    total_recebido = pedidos_base.with_entities(
        db.func.sum(db.case((Pedido.pago == True, Pedido.total), else_=0))
    ).scalar() or 0
    total_a_receber = Decimal(str(total_vendas)) - Decimal(str(total_recebido))

    custo_total = db.session.query(
        db.func.sum(ItemPedido.quantidade * db.func.coalesce(Produto.preco_compra, 0))
    ).join(Pedido, Pedido.id == ItemPedido.pedido_id).join(
        Produto, Produto.id == ItemPedido.produto_id
    ).filter(
        Pedido.data >= inicio_dt,
        Pedido.data <= fim_dt
    ).scalar() or 0

    lucro_total = Decimal(str(total_vendas)) - Decimal(str(custo_total))
    ticket_medio = (Decimal(str(total_vendas)) / total_pedidos) if total_pedidos else Decimal('0')

    top_clientes_q = db.session.query(
        Cliente.nome.label('nome'),
        db.func.count(Pedido.id).label('pedidos'),
        db.func.sum(Pedido.total).label('total'),
        db.func.sum(db.case((Pedido.pago == True, Pedido.total), else_=0)).label('recebido'),
    ).join(Pedido, Pedido.cliente_id == Cliente.id).filter(
        Pedido.data >= inicio_dt,
        Pedido.data <= fim_dt
    ).group_by(
        Cliente.id, Cliente.nome
    ).order_by(
        db.func.sum(Pedido.total).desc()
    ).limit(10).all()

    top_produtos_q = db.session.query(
        Produto.codigo.label('codigo'),
        Produto.nome.label('nome'),
        db.func.sum(ItemPedido.quantidade).label('quantidade'),
        db.func.sum(ItemPedido.subtotal).label('faturamento'),
        db.func.sum(
            ItemPedido.subtotal - (ItemPedido.quantidade * db.func.coalesce(Produto.preco_compra, 0))
        ).label('lucro')
    ).join(ItemPedido, ItemPedido.produto_id == Produto.id).join(
        Pedido, Pedido.id == ItemPedido.pedido_id
    ).filter(
        Pedido.data >= inicio_dt,
        Pedido.data <= fim_dt
    ).group_by(
        Produto.id, Produto.codigo, Produto.nome
    ).order_by(
        db.func.sum(ItemPedido.subtotal).desc()
    ).limit(10).all()

    top_clientes = [{
        'nome': row.nome,
        'pedidos': int(row.pedidos or 0),
        'total': float(row.total or 0),
        'recebido': float(row.recebido or 0),
        'a_receber': float(Decimal(str(row.total or 0)) - Decimal(str(row.recebido or 0))),
    } for row in top_clientes_q]

    top_produtos = [{
        'codigo': row.codigo,
        'nome': row.nome,
        'quantidade': float(row.quantidade or 0),
        'faturamento': float(row.faturamento or 0),
        'lucro': float(row.lucro or 0),
    } for row in top_produtos_q]

    resumo = {
        'total_pedidos': total_pedidos,
        'total_vendas': float(total_vendas),
        'custo_total': float(custo_total),
        'lucro_total': float(lucro_total),
        'ticket_medio': float(ticket_medio),
        'total_recebido': float(total_recebido),
        'total_a_receber': float(total_a_receber),
    }

    return render_template(
        'relatorios.html',
        periodo=periodo,
        data_inicio=data_inicio,
        data_fim=data_fim,
        mes_ref=mes_ref,
        opcoes_meses=opcoes_meses,
        resumo=resumo,
        top_clientes=top_clientes,
        top_produtos=top_produtos,
    )


# ══════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIAS = [
    'AMENDOIM', 'BALA', 'CHICLETE', 'PIRULITO',
    'CHOCOLATE', 'SALGADINHO', 'POTE', 'DIVERSOS',
]

UNIDADES_PRODUTO = ['UN', 'CX', 'PT', 'DP', 'PCT', 'FD', 'BD', 'CT', 'ESP', 'KG']

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
        preco_compra = request.form.get('preco_compra', '0').replace(',', '.') or '0'
        is_ajax   = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if Produto.query.filter_by(codigo=codigo).first():
            if is_ajax:
                return jsonify({'ok': False, 'msg': 'Código já cadastrado!'})
            flash('Código já cadastrado!', 'danger')
            return render_template('produtos/form.html', categorias=CATEGORIAS, form=request.form)

        p = Produto(codigo=codigo, nome=nome, categoria=categoria,
                    preco=Decimal(preco), preco_compra=Decimal(preco_compra),
                    unidade=unidade, descricao=descricao)
        db.session.add(p)
        db.session.commit()

        if is_ajax:
            return jsonify({
                'ok': True,
                'msg': f'Produto <strong>{nome}</strong> cadastrado!',
                'produto': {
                    'id': p.id,
                    'codigo': p.codigo,
                    'nome': p.nome,
                    'categoria': p.categoria,
                    'preco': float(p.preco),
                    'unidade': p.unidade,
                }
            })
        flash(f'Produto <strong>{nome}</strong> cadastrado com sucesso!', 'success')
        return redirect(url_for('produto_novo'))

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

        p.codigo       = codigo_novo
        p.nome         = request.form['nome'].strip().upper()
        p.categoria    = request.form['categoria']
        p.preco        = Decimal(request.form['preco'].replace(',', '.'))
        p.preco_compra = Decimal((request.form.get('preco_compra', '0') or '0').replace(',', '.'))
        p.unidade      = request.form.get('unidade', 'UN').upper()
        p.descricao    = request.form.get('descricao', '').strip()
        p.ativo        = 'ativo' in request.form
        db.session.commit()
        flash('Produto atualizado!', 'success')
        return redirect(url_for('produto_editar', id=p.id))

    return render_template('produtos/form.html', categorias=CATEGORIAS,
                           form={}, produto=p)


@app.route('/produtos/<int:id>/excluir', methods=['POST'])
def produto_excluir(id):
    p = Produto.query.get_or_404(id)
    p.ativo = False
    db.session.commit()
    flash('Produto desativado!', 'warning')
    return redirect(url_for('produtos_lista'))


# ── API de verificação de código duplicado ───────────────────────────────────
@app.route('/api/produtos/checar-codigo')
def api_checar_codigo():
    codigo = request.args.get('codigo', '').strip().upper()
    excluir_id = request.args.get('excluir_id', type=int)
    if not codigo:
        return jsonify({'existe': False})
    query = Produto.query.filter_by(codigo=codigo)
    if excluir_id:
        query = query.filter(Produto.id != excluir_id)
    p = query.first()
    if p:
        return jsonify({'existe': True, 'nome': p.nome, 'id': p.id, 'ativo': p.ativo})
    return jsonify({'existe': False})


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
    return render_template(
        'pedidos/novo.html',
        clientes=clientes,
        categorias=CATEGORIAS,
        unidades_produto=UNIDADES_PRODUTO,
    )


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


@app.route('/pedidos/<int:id>/pago', methods=['POST'])
def pedido_pago(id):
    pedido = Pedido.query.get_or_404(id)
    pedido.pago = not pedido.pago
    db.session.commit()
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

    # Salvar na pasta pdfs/
    pasta_pdfs = os.path.join(os.path.dirname(__file__), 'pdfs')
    os.makedirs(pasta_pdfs, exist_ok=True)
    caminho = os.path.join(pasta_pdfs, nome_arquivo)
    with open(caminho, 'wb') as f:
        f.write(buf.read())
    buf.seek(0)

    return send_file(
        buf,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=nome_arquivo,
    )


# ══════════════════════════════════════════════════════════════════════════════
# BOLETOS
# ══════════════════════════════════════════════════════════════════════════════

EXTENSOES_COMPROVANTE = {'pdf', 'png', 'jpg', 'jpeg'}

def _extensao_permitida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSOES_COMPROVANTE


@app.route('/boletos')
def boletos_lista():
    status    = request.args.get('status', '')
    q         = request.args.get('q', '').strip()
    page      = request.args.get('page', 1, type=int)

    query = Boleto.query
    if status == 'vencido':
        query = query.filter(Boleto.status == 'pendente', Boleto.data_vencimento < date.today())
    elif status:
        query = query.filter(Boleto.status == status)
    if q:
        query = query.filter(Boleto.fornecedor.ilike(f'%{q}%'))

    boletos = query.order_by(Boleto.data_vencimento.asc()).paginate(page=page, per_page=20)
    total_pendente = db.session.query(db.func.sum(Boleto.valor)).filter(Boleto.status == 'pendente').scalar() or 0
    return render_template('boletos/lista.html', boletos=boletos, status=status, q=q,
                           total_pendente=float(total_pendente), hoje=date.today())


@app.route('/boletos/novo', methods=['GET', 'POST'])
def boleto_novo():
    if request.method == 'POST':
        valor           = Decimal(request.form['valor'].replace(',', '.'))
        data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
        observacoes     = request.form.get('observacoes', '').strip()

        b = Boleto(valor=valor, data_vencimento=data_vencimento, observacoes=observacoes)
        db.session.add(b)
        db.session.commit()
        flash('Boleto cadastrado com sucesso!', 'success')
        return redirect(url_for('boletos_lista'))

    return render_template('boletos/form.html', boleto=None, form={})


@app.route('/boletos/<int:id>/editar', methods=['GET', 'POST'])
def boleto_editar(id):
    b = Boleto.query.get_or_404(id)
    if request.method == 'POST':
        b.valor           = Decimal(request.form['valor'].replace(',', '.'))
        b.data_vencimento = datetime.strptime(request.form['data_vencimento'], '%Y-%m-%d').date()
        b.observacoes     = request.form.get('observacoes', '').strip()
        db.session.commit()
        flash('Boleto atualizado!', 'success')
        return redirect(url_for('boletos_lista'))

    return render_template('boletos/form.html', boleto=b, form={})


@app.route('/boletos/<int:id>/pagar', methods=['POST'])
def boleto_pagar(id):
    b = Boleto.query.get_or_404(id)
    data_str = request.form.get('data_pagamento', '')
    b.data_pagamento = datetime.strptime(data_str, '%Y-%m-%d').date() if data_str else date.today()
    b.status = 'pago'

    arquivo = request.files.get('comprovante')
    if arquivo and arquivo.filename and _extensao_permitida(arquivo.filename):
        pasta = app.config['UPLOAD_FOLDER']
        os.makedirs(pasta, exist_ok=True)
        ext      = arquivo.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        arquivo.save(os.path.join(pasta, filename))
        # remove comprovante antigo se existir
        if b.comprovante:
            old = os.path.join(app.config['UPLOAD_FOLDER'], b.comprovante)
            if os.path.exists(old):
                os.remove(old)
        b.comprovante = filename

    db.session.commit()
    flash('Boleto marcado como pago!', 'success')
    return redirect(url_for('boletos_lista'))


@app.route('/boletos/<int:id>/excluir', methods=['POST'])
def boleto_excluir(id):
    b = Boleto.query.get_or_404(id)
    if b.comprovante:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], b.comprovante)
        if os.path.exists(caminho):
            os.remove(caminho)
    db.session.delete(b)
    db.session.commit()
    flash('Boleto excluído!', 'warning')
    return redirect(url_for('boletos_lista'))


@app.route('/boletos/<int:id>/comprovante')
def boleto_comprovante(id):
    b = Boleto.query.get_or_404(id)
    if not b.comprovante:
        abort(404)
    caminho = os.path.join(app.config['UPLOAD_FOLDER'], b.comprovante)
    if not os.path.exists(caminho):
        abort(404)
    return send_file(caminho, as_attachment=False)


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
