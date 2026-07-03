import os
import json
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List
from supabase import create_client, Client

# Inicialização do Cliente Oficial do Supabase
SUPABASE_URL = "https://ojiutbtyaxmpwstgnmnn.supabase.co"
SUPABASE_KEY = "sb_publishable_c-OH1QCwqmsWCmDj9rMq-w_eaqTJgDQ"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@dataclass
class Gasto:
    """
    Representa um gasto ou receita individual.

    Atributos:
        id (str): Identificador único do gasto (gerado automaticamente via UUID4).
        descricao (str): Descrição do lançamento (ex: 'Supermercado', 'Salário').
        valor (float): Valor monetário.
        categoria (str): Categoria do lançamento (ex: 'Alimentação', 'Receita').
        data (date): Data em que o lançamento foi realizado.
    """
    descricao: str
    valor: float
    categoria: str
    data: date
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


class GerenciadorFinancas:
    """
    Gerencia uma lista de gastos pessoais integrada ao Supabase, isolando os dados
    de cada usuário utilizando o identificador UUID do Supabase.
    """

    def __init__(self, user_id: str = None, access_token: str = None, supabase_client: Client = None):
        self.user_id = user_id
        self.access_token = access_token
        self.supabase = supabase_client if supabase_client is not None else supabase
        self.gastos: List[Gasto] = []

    def adicionar_gasto(self, descricao: str, valor: float, categoria: str, data: date) -> Gasto:
        """
        Cria e adiciona um novo lançamento, salvando-o diretamente no Supabase se houver user_id.
        """
        if valor <= 0:
            raise ValueError("O valor do lançamento deve ser maior que zero.")

        gasto = Gasto(descricao=descricao, valor=valor, categoria=categoria, data=data)

        if self.user_id:
            self.salvar_gasto(
                descricao=gasto.descricao,
                valor=gasto.valor,
                categoria=gasto.categoria,
                data_lancamento=gasto.data,
                user_id=self.user_id
            )

        self.gastos.append(gasto)
        return gasto

    def salvar_gasto(self, descricao, valor, categoria, data_lancamento, user_id):
        dados = {
            "descricao": descricao,
            "valor": float(valor),
            "categoria": categoria,
            "data": str(data_lancamento),
            "user_id": str(user_id) # Forçar string pura do UUID
        }
        try:
            # O .execute() garante o envio imediato e persistente para o banco
            resposta = self.supabase.table("gastos").insert(dados).execute()
            return resposta
        except Exception as e:
            print(f"Erro ao salvar no Supabase: {e}")
            return None

    def calcular_saldo_restante(self, renda_mensal: float) -> float:
        """
        Calcula o saldo restante subtraindo o total acumulado de gastos da renda mensal.
        """
        if renda_mensal < 0:
            raise ValueError("A renda mensal não pode ser negativa.")

        total_gastos = sum(gasto.valor for gasto in self.gastos if gasto.categoria != "Receita")
        return renda_mensal - total_gastos

    def agrupar_e_somar_por_categoria(self) -> Dict[str, float]:
        """
        Agrupa todos os gastos cadastrados por categoria e soma seus valores.
        """
        agrupado: Dict[str, float] = {}
        for gasto in self.gastos:
            if gasto.categoria != "Receita":
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

    def carregar_dados(self, user_id) -> None:
        """
        Carrega os lançamentos do Supabase filtrando pelo user_id do usuário logado.
        """
        try:
            resposta = self.supabase.table("gastos").select("*").eq("user_id", str(user_id)).execute()
            dados = resposta.data if resposta.data else []
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
        except Exception as e:
            print(f"Erro ao ler do Supabase: {e}")
            self.gastos = []

    def remover_gasto(self, id_gasto: str) -> bool:
        """
        Remove um lançamento do banco Supabase e da memória local.
        """
        if self.user_id:
            try:
                self.supabase.table("gastos").delete().eq("id", id_gasto).eq("user_id", self.user_id).execute()
            except Exception:
                pass

        original_len = len(self.gastos)
        self.gastos = [gasto for gasto in self.gastos if gasto.id != id_gasto]
        return len(self.gastos) < original_len

    def obter_meses_disponiveis(self) -> List[str]:
        """
        Retorna uma lista ordenada de strings 'MM/AAAA' correspondentes aos meses
        em que existem lançamentos cadastrados.
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
        Retorna uma lista de lançamentos filtrada pela string 'MM/AAAA'.
        """
        filtrados = []
        for g in self.gastos:
            if g.data.strftime("%m/%Y") == mes_ano_str:
                filtrados.append(g)
        return filtrados

    def agrupar_por_categoria_ano(self, ano: int) -> Dict[str, float]:
        """
        Filtra todos os lançamentos pelo ano selecionado e os agrupa somando por categoria.
        """
        agrupado: Dict[str, float] = {}
        for g in self.gastos:
            if g.data.year == ano:
                cat_normalizada = g.categoria.strip().capitalize()
                agrupado[cat_normalizada] = agrupado.get(cat_normalizada, 0.0) + g.valor
        return agrupado


if __name__ == "__main__":
    print("--- Inicializando Gerenciador de Finanças (Supabase SDK Mode) ---")
    gerenciador = GerenciadorFinancas(user_id="demo_clerk_id")
    print("Objeto configurado com sucesso!")
