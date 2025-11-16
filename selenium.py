import sys
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# ------------------------------
# Carrega variáveis do .env (login e senha)
# ------------------------------
load_dotenv()
LOGIN = os.getenv("LOGIN")
SENHA = os.getenv("SENHA")

# ------------------------------
# Configurações iniciais
# ------------------------------
URL_LOGIN = ""
URL_QUADRO_AVISOS = ""
URL_TESTE_SESSAO = ""
PASTA = "pdf_files"

os.makedirs(PASTA, exist_ok=True)

# ------------------------------
# Funções auxiliares
# ------------------------------
def verificar_pdf(caminho_pdf):
    if os.path.exists(caminho_pdf):
        try:
            PdfReader(caminho_pdf)
            return True
        except:
            return False
    return False

def sessao_valida(sessao):
    try:
        resposta = sessao.get(URL_TESTE_SESSAO, timeout=10)
        if resposta.status_code == 200 and "login" not in resposta.url.lower():
            return True
    except Exception as e:
        print(f" Erro ao verificar sessão: {e}")
    return False

# ------------------------------
# Classe Navegador
# ------------------------------
class Navegador:
    def __init__(self, driver, options):
        self.service = Service(driver)
        self.browser = webdriver.Chrome(service=self.service, options=options)

    def abrir_pagina(self, url_pagina):
        self.browser.get(url_pagina)

    def logar(self, username, password):

        wait = WebDriverWait(self.browser, 20)  # espera até 20s


        inicio = time.time()

        wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "ssoFrame")))

        fim = time.time()

        tempo_espera = (fim - inicio) / 60
        print(f"O iframe levou {tempo_espera:.2f} minutos para carregar.")

        wait.until(EC.presence_of_element_located((By.ID, "username")))
        wait.until(EC.presence_of_element_located((By.ID, "password")))
        wait.until(EC.presence_of_element_located((By.ID, "kc-login")))   

        self.browser.find_element(By.ID, 'username').send_keys(username)
        self.browser.find_element(By.ID, 'password').send_keys(password)
        self.browser.find_element(By.ID, 'kc-login').click()
        
        
        # sai do frame para esperar a próxima tela
        self.browser.switch_to.default_content()

        
        wait.until(EC.presence_of_element_located((By.ID, "pageBody")))

    def pegar_cookies(self):
        session = requests.Session()
        session.headers["User-Agent"] = self.browser.execute_script("return navigator.userAgent")
        for cookie in self.browser.get_cookies():
            session.cookies.set(domain=cookie["domain"], name=cookie["name"], value=cookie["value"])
        return session

    def baixar_pdf(self, sessao, url):
        id_processo = url.split("/")[-2]
        nome_arquivo = f"{PASTA}/peticao_inicial_{id_processo}.pdf"
        resposta = sessao.get(url)
        with open(nome_arquivo, "wb") as f:
            f.write(resposta.content)
        return nome_arquivo

    def fechar_navegador(self):
        self.browser.quit()

# ------------------------------
# Execução principal
# ------------------------------
if __name__ == '__main__':
    if len(sys.argv) > 1:
        urls = sys.argv[1].split(",")
    else:
        print("URLs dos PDFs não foram fornecidas!")
        sys.exit()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    navegador = Navegador('./chromedriver', options)

    # Login
    navegador.abrir_pagina(URL_LOGIN)
    navegador.logar(LOGIN, SENHA)

    sessao = navegador.pegar_cookies()

    for URL in urls:
        URL = URL.strip()
        if not URL:
            continue

        print(f" Baixando: {URL}")
        nome_arquivo = navegador.baixar_pdf(sessao, URL)
        time.sleep(1)

        sucesso = verificar_pdf(nome_arquivo)
        tentativas = 0

        while not sucesso and tentativas < 3:
            if tentativas == 0 and not sessao_valida(sessao):
                print(" Sessão inválida! Refazendo login...")
                navegador.abrir_pagina(URL_LOGIN)
                navegador.logar(LOGIN, SENHA)
                sessao = navegador.pegar_cookies()

            print(f" Erro ao validar {nome_arquivo}, tentando novamente... ({tentativas+1}/3)")
            time.sleep(1)
            nome_arquivo = navegador.baixar_pdf(sessao, URL)
            sucesso = verificar_pdf(nome_arquivo)
            tentativas += 1

        if sucesso:
            with open("successfull.txt", "a") as f:
                f.write(f"{nome_arquivo}\n")
            print(f" Sucesso: {nome_arquivo}")
        else:
            with open("unsuccessfull.txt", "a") as f:
                f.write(f"{URL}\n")
            if os.path.exists(nome_arquivo):
                os.remove(nome_arquivo)
            print(f" Falha: {URL} (registrado em unsuccessfull.txt)")

    navegador.fechar_navegador()
