from flask import Flask, request, jsonify, render_template_string
from sheets import cadastrar_cliente, listar_clientes
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── HTML do formulário de captação ──────────────────────────────────────────
FORMULARIO_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cadastro de Cliente</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .card {
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 480px;
        }
        h1 { color: #1a1a2e; margin-bottom: 8px; font-size: 24px; }
        p  { color: #666; margin-bottom: 28px; font-size: 14px; }
        label { display: block; font-size: 13px; font-weight: 600;
                color: #444; margin-bottom: 6px; }
        input {
            width: 100%; padding: 12px 14px; border: 1.5px solid #ddd;
            border-radius: 8px; font-size: 15px; margin-bottom: 18px;
            transition: border-color 0.2s;
        }
        input:focus { outline: none; border-color: #4f46e5; }
        button {
            width: 100%; padding: 14px; background: #4f46e5;
            color: white; border: none; border-radius: 8px;
            font-size: 16px; font-weight: 600; cursor: pointer;
        }
        button:hover { background: #4338ca; }
        #msg { margin-top: 18px; padding: 12px; border-radius: 8px;
               text-align: center; font-weight: 600; display: none; }
        .sucesso { background: #d1fae5; color: #065f46; }
        .erro    { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
<div class="card">
    <h1>📋 Cadastro de Cliente</h1>
    <p>Preencha os dados abaixo para se cadastrar.</p>

    <label>Nome completo *</label>
    <input type="text" id="nome" placeholder="João Silva" required>

    <label>E-mail *</label>
    <input type="email" id="email" placeholder="joao@email.com" required>

    <label>Telefone / WhatsApp *</label>
    <input type="tel" id="telefone" placeholder="(11) 99999-9999" required>

    <label>Empresa</label>
    <input type="text" id="empresa" placeholder="Nome da empresa (opcional)">

    <button onclick="enviarCadastro()">Cadastrar agora</button>
    <div id="msg"></div>
</div>

<script>
async function enviarCadastro() {
    const nome     = document.getElementById('nome').value.trim()
    const email    = document.getElementById('email').value.trim()
    const telefone = document.getElementById('telefone').value.trim()
    const empresa  = document.getElementById('empresa').value.trim()
    const msg      = document.getElementById('msg')

    // Validação básica no frontend
    if (!nome || !email || !telefone) {
        msg.className = 'erro'; msg.style.display = 'block'
        msg.textContent = '⚠️ Preencha todos os campos obrigatórios.'
        return
    }

    try {
        const resposta = await fetch('/cadastrar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, email, telefone, empresa })
        })
        const dados = await resposta.json()

        if (resposta.ok) {
            msg.className = 'sucesso'; msg.style.display = 'block'
            msg.textContent = '✅ Cadastro realizado! Em breve você receberá uma confirmação.'
        } else {
            throw new Error(dados.erro)
        }
    } catch (e) {
        msg.className = 'erro'; msg.style.display = 'block'
        msg.textContent = '❌ Erro: ' + e.message
    }
}
</script>
</body>
</html>
"""

# ── Rotas ────────────────────────────────────────────────────────────────────

@app.route('/')
def formulario():
    """Exibe o formulário de cadastro"""
    return render_template_string(FORMULARIO_HTML)


@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    """Recebe os dados do formulário, salva na planilha e dispara o n8n"""
    dados = request.get_json()

    # Validação no backend
    campos_obrigatorios = ['nome', 'email', 'telefone']
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400

    # Salva no Google Sheets
    cliente = cadastrar_cliente(dados)

    # Dispara o webhook do n8n
    disparar_n8n(cliente)

    return jsonify({'mensagem': 'Cliente cadastrado com sucesso!', 'cliente': cliente}), 201


@app.route('/clientes', methods=['GET'])
def clientes():
    """Lista todos os clientes (para conferir os dados)"""
    return jsonify(listar_clientes())


def disparar_n8n(cliente: dict):
    """Envia os dados do cliente para o webhook do n8n"""
    webhook_url = os.getenv('WEBHOOK_N8N')
    try:
        requests.post(webhook_url, json=cliente, timeout=5)
    except Exception as e:
        print(f'[AVISO] Webhook n8n falhou: {e}')


if __name__ == '__main__':
    # debug=True reinicia o servidor automaticamente ao salvar o arquivo
    app.run(debug=True, port=5000)