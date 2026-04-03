"""
Script de configuração inicial do banco de dados JP Doces.
Execute: python setup.py
"""
import sys
import os
from dotenv import load_dotenv
load_dotenv()

def main():
    print("=" * 55)
    print("  JP DOCES -- Configuracao Inicial do Banco")
    print("=" * 55)

    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', '3306'))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASS = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'jp_doces')

    print(f"Conectando como '{DB_USER}' em {DB_HOST}:{DB_PORT} ...")

    # 1. Cria banco de dados se não existir
    try:
        import pymysql
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASS,
            charset='utf8mb4'
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        print(f"Banco de dados '{DB_NAME}' verificado/criado!")
    except Exception as e:
        print(f"❌ Erro ao criar banco: {e}")
        print("   Verifique se o MySQL está rodando e as credenciais no .env")
        sys.exit(1)

    # 2. Cria tabelas via SQLAlchemy
    try:
        from app import app
        from extensions import db
        with app.app_context():
            db.create_all()
        print("✅ Tabelas criadas com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        sys.exit(1)

    # 3. Seed de produtos do catálogo
    try:
        from app import app
        from extensions import db
        from models import Produto
        from seed_data import PRODUTOS_SEED
        with app.app_context():
            inseridos = 0
            for p in PRODUTOS_SEED:
                if not Produto.query.filter_by(codigo=str(p['codigo'])).first():
                    db.session.add(Produto(**{**p, 'codigo': str(p['codigo'])}))
                    inseridos += 1
            db.session.commit()
        print(f"✅ {inseridos} produtos do catálogo importados!")
    except Exception as e:
        print(f"❌ Erro ao importar produtos: {e}")
        sys.exit(1)

    print()
    print("=" * 55)
    print("  ✅  Sistema pronto! Execute: python app.py")
    print("  🌐  Acesse: http://localhost:5000")
    print("=" * 55)


if __name__ == '__main__':
    main()
