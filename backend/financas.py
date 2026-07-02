import json
import uuid
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
    Gerencia uma lista de gastos pessoais e fornece funções para análise financeira.
    """

    def __init__(self):
        self.gastos: List[Gasto] = []

    def adicionar_gasto(self, descricao: str, valor: float, categoria: str, data: date) -> Gasto:
        """
        Cria e adiciona um novo gasto à lista de controle.

        Args:
            descricao (str): Descrição do gasto.
            valor (float): Valor do gasto (deve ser maior que zero).
            categoria (str): Categoria do gasto.
            data (date): Data do gasto.

        Returns:
            Gasto: O objeto Gasto criado e inserido na lista.
        """
        if valor <= 0:
            raise ValueError("O valor do gasto deve ser maior que zero.")

        gasto = Gasto(descricao=descricao, valor=valor, categoria=categoria, data=data)
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

        As categorias têm os nomes padronizados (capitalizados e sem espaços extras nas pontas)
        para garantir que entradas similares sejam agrupadas juntas.

        Returns:
            Dict[str, float]: Um dicionário com as categorias como chaves e a soma dos gastos como valores.
        """
        agrupado: Dict[str, float] = {}
        for gasto in self.gastos:
            # Padroniza a categoria para evitar diferenças por letras maiúsculas/minúsculas ou espaços
            cat_normalizada = gasto.categoria.strip().capitalize()
            agrupado[cat_normalizada] = agrupado.get(cat_normalizada, 0.0) + gasto.valor
        return agrupado

    def salvar_dados(self, caminho_arquivo: str) -> None:
        """
        Converte a lista de objetos 'Gasto' em formato JSON e salva em um arquivo.

        As datas dos gastos (tipo date) são convertidas para string no formato ISO (YYYY-MM-DD).

        Args:
            caminho_arquivo (str): Caminho do arquivo onde os dados serão salvos.
        """
        dados = []
        for gasto in self.gastos:
            dados.append({
                "id": gasto.id,
                "descricao": gasto.descricao,
                "valor": gasto.valor,
                "categoria": gasto.categoria,
                "data": gasto.data.isoformat()  # Converte date para string (AAAA-MM-DD)
            })

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)

    def carregar_dados(self, caminho_arquivo: str) -> None:
        """
        Lê um arquivo JSON, converte as strings de data de volta para objetos date,
        e preenche a lista self.gastos.

        Args:
            caminho_arquivo (str): Caminho do arquivo de onde os dados serão carregados.
        """
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)

        self.gastos = []
        for item in dados:
            gasto = Gasto(
                id=item["id"],
                descricao=item["descricao"],
                valor=item["valor"],
                categoria=item["categoria"],
                data=date.fromisoformat(item["data"])  # Converte string ISO de volta para date
            )
            self.gastos.append(gasto)

    def remover_gasto(self, id_gasto: str) -> bool:
        """
        Remove um gasto da lista baseado no seu ID único.

        Args:
            id_gasto (str): O ID único do gasto a ser removido.

        Returns:
            bool: True se o gasto foi encontrado e removido, False caso contrário.
        """
        original_len = len(self.gastos)
        self.gastos = [gasto for gasto in self.gastos if gasto.id != id_gasto]
        return len(self.gastos) < original_len


# Demonstração de uso do módulo (executada quando o arquivo roda diretamente)
if __name__ == "__main__":
    print("--- Inicializando Gerenciador de Finanças ---")
    gerenciador = GerenciadorFinancas()
    arquivo_dados = "dados_financeiros.json"

    # 1. Adicionando gastos de teste
    print("\n1. Adicionando gastos na memória...")
    gerenciador.adicionar_gasto("Compras de supermercado", 350.50, "Alimentação", date(2026, 7, 1))
    gerenciador.adicionar_gasto("Combustível", 150.00, "Transporte", date(2026, 7, 2))
    gerenciador.adicionar_gasto("Jantar fora", 120.00, "alimentação", date(2026, 7, 2))
    gerenciador.adicionar_gasto("Assinatura de streaming", 39.90, "Entretenimento", date(2026, 7, 2))

    for g in gerenciador.gastos:
        print(f"   [Memória] ID={g.id[:8]}... | Descrição={g.descricao} | Valor=R${g.valor:.2f} | Categoria={g.categoria} | Data={g.data}")

    # 2. Salvando os dados em JSON
    print(f"\n2. Salvando dados em '{arquivo_dados}'...")
    gerenciador.salvar_dados(arquivo_dados)
    print("   Dados salvos com sucesso!")

    # 3. Limpando a lista na memória para provar que o carregamento funciona
    print("\n3. Limpando a lista de gastos da memória...")
    gerenciador.gastos = []
    print(f"   Quantidade de gastos na memória: {len(gerenciador.gastos)}")

    # 4. Carregando os dados de volta do arquivo
    print(f"\n4. Carregando dados a partir de '{arquivo_dados}'...")
    gerenciador.carregar_dados(arquivo_dados)
    print(f"   Quantidade de gastos carregados: {len(gerenciador.gastos)}")

    for g in gerenciador.gastos:
        print(f"   [Carregado] ID={g.id[:8]}... | Descrição={g.descricao} | Valor=R${g.valor:.2f} | Categoria={g.categoria} | Data={g.data} (Tipo data: {type(g.data).__name__})")

    # 5. Calculando saldo e agrupando (usando os dados carregados)
    renda = 3500.00
    saldo = gerenciador.calcular_saldo_restante(renda)
    print(f"\n5. Cálculo de Saldo (com dados carregados):")
    print(f"   Renda mensal: R${renda:.2f}")
    print(f"   Saldo restante: R${saldo:.2f}")

    gastos_por_categoria = gerenciador.agrupar_e_somar_por_categoria()
    print("\n6. Gastos agrupados por categoria (com dados carregados):")
    for categoria, total in gastos_por_categoria.items():
        print(f"   - {categoria}: R${total:.2f}")

