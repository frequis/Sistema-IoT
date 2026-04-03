"""Popula o banco com 30 leituras de exemplo para testes e entrega."""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from database import init_db, inserir_leitura

TOTAL = 30

def popular():
    init_db()
    for i in range(TOTAL):
        temp    = round(random.uniform(18.0, 35.0), 1)
        umidade = round(random.uniform(40.0, 90.0), 1)
        pressao = round(random.uniform(1008.0, 1025.0), 1) if random.random() > 0.2 else None
        inserir_leitura(temp, umidade, pressao)
    print(f"{TOTAL} leituras inseridas com sucesso.")

if __name__ == "__main__":
    popular()
