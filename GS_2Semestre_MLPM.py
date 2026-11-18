import csv
import datetime
import json
import os
import sys
import textwrap
import time

PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_BASE = os.path.join(PASTA, "base_conhecimento.json")
ARQ_METRICAS = os.path.join(PASTA, "metricas.csv")

LARGURA = 72
LIMITE_ENTRADA = 20

AVISO = ("Protótipo educacional. Não é canal oficial do INEP nem do governo. "
         "Confirme informações importantes nos canais oficiais.")



CAMPOS = ["data", "evento", "id_resposta", "tempo_s", "util", "facilidade"]


def registrar(**campos):
    novo = not os.path.exists(ARQ_METRICAS)
    with open(ARQ_METRICAS, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS, delimiter=";")
        if novo:
            w.writeheader()
        linha = {c: "" for c in CAMPOS}
        linha["data"] = datetime.date.today().isoformat()
        linha.update(campos)
        w.writerow(linha)


def resumo():
    if not os.path.exists(ARQ_METRICAS):
        print("Ainda não há metricas.csv. Use o assistente com algumas pessoas primeiro.")
        return
    with open(ARQ_METRICAS, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    consultas = [l for l in linhas if l["evento"] == "consulta"]
    tempos = sorted(float(l["tempo_s"]) for l in consultas if l["tempo_s"])
    util = [l["util"] for l in consultas if l["util"] in ("s", "n")]
    fac = [int(l["facilidade"]) for l in linhas if l["evento"] == "avaliacao" and l["facilidade"].isdigit()]
    print("RESUMO DOS INDICADORES")
    print(f"  Respostas mostradas: {len(consultas)}")
    if tempos:
        print(f"  Tempo para achar a informação: média {sum(tempos) / len(tempos):.1f} s"
              f" | mediana {tempos[len(tempos) // 2]:.1f} s")
    if util:
        print(f"  Orientações marcadas como úteis: {100 * util.count('s') / len(util):.0f}%"
              f" ({len(util)} avaliações)")
    if fac:
        print(f"  Facilidade de uso (1 a 5): média {sum(fac) / len(fac):.2f} ({len(fac)} avaliações)")


def dizer(texto="", recuo=""):
    if not texto:
        print()
        return
    print(textwrap.fill(texto, width=LARGURA, initial_indent=recuo, subsequent_indent=recuo))


def perguntar(texto):
    try:
        return input(texto).strip()
    except EOFError:
        raise KeyboardInterrupt


def mostrar_resposta(e):
    print()
    print("-" * LARGURA)
    dizer(e["titulo"].upper())
    print()
    dizer(e["resposta"])
    print()
    dizer("Fonte: " + e["fonte"])
    dizer("Verificado em: " + e["verificado_em"])
    if e.get("limite"):
        dizer("Limitação: " + e["limite"])
    dizer("Aviso: " + AVISO)
    print("-" * LARGURA)


def avaliar_utilidade(id_resp, t_ini):
    r = perguntar("Esta resposta ajudou? (S = sim, N = não, Enter = pular): ").lower()
    util = r if r in ("s", "n") else ""
    registrar(evento="consulta", id_resposta=id_resp, tempo_s=f"{time.time() - t_ini:.1f}", util=util)


def entrada_invalida(texto, maximo, no_menu_principal=True):
    print()
    if not texto:
        dizer("Você não digitou nada. Digite um dos números do menu.")
    elif len(texto) > LIMITE_ENTRADA:
        dizer("Texto muito longo. Este assistente funciona só com números: digite um dos números do menu.")
    else:
        extra = " (A = ajuda, S = sair)" if no_menu_principal else " (0 = voltar)"
        dizer(f"Opção inválida. Digite um número de 1 a {maximo}.{extra}")



def mostrar_menu(base):
    print()
    dizer("MENU PRINCIPAL - escolha o assunto digitando o número:")
    for num, nome in base["categorias"].items():
        dizer(f"{num}) {nome}", recuo="  ")
    dizer("A) Ajuda", recuo="  ")
    dizer("S) Sair", recuo="  ")


def mostrar_ajuda():
    print()
    dizer("COMO USAR")
    dizer("- Digite o NÚMERO do assunto e aperte Enter. Depois escolha o tópico que quer ler.")
    dizer("- Digite 0 para voltar ao menu anterior.")
    dizer("- Você não precisa digitar nenhum dado pessoal. Nada do que você digita é guardado.")
    dizer("- Este assistente só conhece o Dicionário de Variáveis do ENEM 2025. "
          "Ele não informa inscrição, datas, taxas ou isenção.")
    dizer("Aviso: " + AVISO)


def tela_categoria(base, num):
    itens = [e for e in base["entradas"] if e["categoria"] == num]
    while True:
        print()
        dizer(base["categorias"][num].upper())
        for i, e in enumerate(itens, 1):
            dizer(f"{i}) {e['titulo']}", recuo="  ")
        dizer("0) Voltar ao menu principal", recuo="  ")
        t_ini = time.time()
        r = perguntar("Escolha um número: ")
        if r == "0":
            return
        if r.isdigit() and 1 <= int(r) <= len(itens):
            e = itens[int(r) - 1]
            mostrar_resposta(e)
            avaliar_utilidade(e["id"], t_ini)
        else:
            entrada_invalida(r, len(itens), no_menu_principal=False)


def conversar(base):
    print("=" * LARGURA)
    dizer("ASSISTENTE ENEM - protótipo educacional")
    dizer("Tiro dúvidas sobre o ENEM 2025 usando o dicionário de dados oficial do INEP.")
    dizer("Aviso: " + AVISO)
    dizer("Não peço dados pessoais e não guardo o que você digita.")
    print("=" * LARGURA)
    try:
        while True:
            mostrar_menu(base)
            r = perguntar("> ")
            baixo = r.lower()
            if baixo in ("s", "sair"):
                break
            if baixo in ("a", "ajuda"):
                mostrar_ajuda()
            elif r in base["categorias"]:
                tela_categoria(base, r)
            else:
                entrada_invalida(r, len(base["categorias"]))
    except KeyboardInterrupt:
        print()
    print()
    dizer("De 1 a 5, quão fácil foi usar este assistente? (1 = muito difícil, 5 = muito fácil)")
    try:
        f = perguntar("Sua nota (Enter para pular): ")
        if f in ("1", "2", "3", "4", "5"):
            registrar(evento="avaliacao", facilidade=f)
    except KeyboardInterrupt:
        print()
    dizer("Obrigado! Até a próxima.")


def main():
    if not os.path.exists(ARQ_BASE):
        raise SystemExit(f"Não encontrei base_conhecimento.json na pasta {PASTA}")
    with open(ARQ_BASE, encoding="utf-8") as f:
        base = json.load(f)
    if "--resumo" in sys.argv:
        resumo()
    else:
        conversar(base)


if __name__ == "__main__":
    main()
