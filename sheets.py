import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

# Escopos de permissão necessários
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def conectar_sheets():
    """Conecta na planilha e retorna o objeto worksheet"""
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(os.getenv('GOOGLE_SHEET_NAME')).sheet1
    return sheet

def proximo_id(sheet):
    """Pega todos os registros e calcula o próximo ID"""
    registros = sheet.get_all_records()
    if not registros:
        return 1
    return len(registros) + 1

def cadastrar_cliente(dados: dict) -> dict:
    """
    Insere uma nova linha na planilha com os dados do cliente
    Retorna o cliente com o ID gerado
    """
    sheet = conectar_sheets()
    novo_id = proximo_id(sheet)

    from datetime import datetime
    linha = [
        novo_id,
        dados['nome'],
        dados['email'],
        dados['telefone'],
        dados.get('empresa', ''),          # .get() usa valor vazio se não existir
        datetime.now().strftime('%d/%m/%Y %H:%M'),
        'Novo'
    ]

    sheet.append_row(linha)  # adiciona a linha no final da planilha

    dados['id'] = novo_id
    dados['status'] = 'Novo'
    return dados

def listar_clientes() -> list:
    """Retorna todos os clientes da planilha como lista de dicionários"""
    sheet = conectar_sheets()
    return sheet.get_all_records()