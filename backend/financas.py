import os
import json
import uuid
import requests
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List


@dataclass
class Gasto:
    """
    Representa um gasto individual.

    Atributos:
        id (str): Identificador único do gasto (gerado automaticamente via UUID4).
        descricao (str): Descrição do gasto (ex: 'Supermercado', 'Gasolina').
        valor (float): Valor monetário do gasto.
        categoria (str): Categoria do gasto (ex: 'Alimentação', 'Transporte').
        data (date): Data em que o gasto foi realizado.
    """
    descricao: str
    valor: float
    categoria: str
    data: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class GerenciadorFinancas:
    """
    Gerencia uma lista de gastos pessoais integrada ao Supabase, isolando os dados
    de cada usuário utilizando o identificador do Clerk.
    """

    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.gastos: List[Gasto] = []
        self.api_url = "https://ojiutbtyaxmpwstgnmnn.supabase.co/rest/v1/gastos"
        self.headers = {
            "apikey": "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
            "Authorization": "Bearer sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def adicionar_gasto(self, descricao: str, valor: float, categoria: str, data: date) -> Gasto:
        """
        Cria e adiciona um novo gasto, salvando-o diretamente no Supabase se houver user_id.

        Args:
            descricao (str): Descrição do gasto.
            valor (float): Valor do gasto (deve ser maior que zero).
            categoria (str): Categoria do gasto.
            data (date): Data do gasto.

        Returns:
            Gasto: O objeto Gasto criado e inserido.
        """
        if valor <= 0:
            raise ValueError("O valor do gasto deve ser maior que zero.")

        gasto = Gasto(descricao=descricao, valor=valor, categoria=categoria, data=data)

        if self.user_id:
            payload = {
                "id": gasto.id,
                "descricao": gasto.descricao,
                "valor": gasto.valor,
                "categoria": gasto.categoria,
                "data": gasto.data.isoformat(),
                "user_id": self.user_id
            }
            try:
                requests.post(self.api_url, headers=self.headers, json=payload)
            except Exception:
                pass

        self.gastos.append(gasto)
        return gasto

    def calcular_saldo_restante(self, renda_mensal: float) -> float:
        """
        Calcula o saldo restante subtraindo o total acumulado de gastos da renda mensal.

        Args:
            renda_mensal (float): A renda total mensal disponível.

        Returns:
            float: O saldo restante após subtrair todos os gastos cadastrados.
        """
        if renda_mensal < 0:
            raise ValueError("A renda mensal não pode ser negativa.")

        total_gastos = sum(gasto.valor for gasto in self.gastos)
        return renda_mensal - total_gastos

    def agrupar_e_somar_por_categoria(self) -> Dict[str, float]:
        """
        Agrupa todos os gastos cadastrados por categoria e soma seus valores.

        Returns:
            Dict[str, float]: Um dicionário com as categorias como chaves e a soma dos gastos como valores.
        """
        agrupado: Dict[str, float] = {}
        for gasto in self.gastos:
            cat_normalizada = gasto.categoria.strip().capitalize()
            agrupado[cat_normalizada] = agrupado.get(cat_normalizada, 0.0) + gasto.valor
        return agrupado

    def salvar_dados(self, caminho_arquivo: str = None) -> None:
        """
        No-op para o Supabase (já salvamos no adicionar), mas salva localmente como cache
        de backup se o caminho for fornecido.
        """
        if caminho_arquivo:
            dados = []
            for gasto in self.gastos:
                dados.append({
                    "id": gasto.id,
                    "descricao": gasto.descricao,
                    "valor": gasto.valor,
                    "categoria": gasto.categoria,
                    "data": gasto.data.isoformat()
                })
            try:
                with open(caminho_arquivo, "w", encoding="utf-8") as f:
                    json.dump(dados, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

    def carregar_dados(self, caminho_arquivo: str = None) -> None:
        """
        Carrega os gastos do Supabase filtrando pelo user_id do Clerk do usuário.
        Se não estiver autenticado e houver arquivo local, carrega localmente.
        """
        if self.user_id:
            try:
                url = f"{self.api_url}?user_id=eq.{self.user_id}"
                response = requests.get(url, headers=self.headers)
                if response.status_code == 200:
                    dados = response.json()
                    self.gastos = []
                    for item in dados:
                        gasto = Gasto(
                            id=item["id"],
                            descricao=item["descricao"],
                            valor=float(item["valor"]),
                            categoria=item["categoria"],
                            data=date.fromisoformat(item["data"])
                        )
                        self.gastos.append(gasto)
                else:
                    self.gastos = []
            except Exception:
                self.gastos = []
        elif caminho_arquivo and os.path.exists(caminho_arquivo):
            try:
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.gastos = []
                for item in dados:
                    gasto = Gasto(
                        id=item["id"],
                        descricao=item["descricao"],
                        valor=item["valor"],
                        categoria=item["categoria"],
                        data=date.fromisoformat(item["data"])
                    )
                    self.gastos.append(gasto)
            except Exception:
                self.gastos = []

    def remover_gasto(self, id_gasto: str) -> bool:
        """
        Remove um gasto do banco Supabase e da memória local.

        Args:
            id_gasto (str): O ID único do gasto a ser removido.

        Returns:
            bool: True se o gasto foi removido da memória local.
        """
        if self.user_id:
            try:
                url = f"{self.api_url}?id=eq.{id_gasto}"
                requests.delete(url, headers=self.headers)
            except Exception:
                pass

        original_len = len(self.gastos)
        self.gastos = [gasto for gasto in self.gastos if gasto.id != id_gasto]
        return len(self.gastos) < original_len

    def obter_meses_disponiveis(self) -> List[str]:
        """
        Retorna uma lista ordenada de strings 'MM/AAAA' correspondentes aos meses
        em que existem gastos cadastrados.
        """
        meses = set()
        hoje = date.today()
        meses.add(hoje.strftime("%m/%Y"))

        for g in self.gastos:
            meses.add(g.data.strftime("%m/%Y"))

        # Ordena cronologicamente
        def parse_date(m_ano):
            m, a = map(int, m_ano.split("/"))
            return (a, m)

        return sorted(list(meses), key=parse_date)

    def filtrar_por_mes_ano(self, mes_ano_str: str) -> List[Gasto]:
        """
        Retorna uma lista de gastos filtrada pela string 'MM/AAAA'.
        """
        filtrados = []
        for g in self.gastos:
            if g.data.strftime("%m/%Y") == mes_ano_str:
                filtrados.append(g)
        return filtrados

    def agrupar_por_categoria_ano(self, ano: int) -> Dict[str, float]:
        """
        Filtra todos os gastos pelo ano selecionado e os agrupa somando por categoria.
        """
        agrupado: Dict[str, float] = {}
        for g in self.gastos:
            if g.data.year == ano:
                cat_normalizada = g.categoria.strip().capitalize()
                agrupado[cat_normalizada] = agrupado.get(cat_normalizada, 0.0) + g.valor
        return agrupado


# Demonstração de uso do módulo
if __name__ == "__main__":
    print("--- Inicializando Gerenciador de Finanças (Supabase SaaS Mode) ---")
    gerenciador = GerenciadorFinancas(user_id="demo_clerk_id")
    print("Objeto configurado com sucesso!")
