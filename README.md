# googletasks-widget

Widget de desktop para GNOME que exibe suas tarefas pendentes do Google Tasks, com tema escuro, clicável e atualização automática.

## Funcionalidades

- Exibe todas as tarefas pendentes de todas as listas, agrupadas por lista
- Cada lista recebe uma cor diferente
- Destaque por prazo: vencida (vermelho), hoje (amarelo), em breve ≤3d (laranja), normal (cinza)
- Tarefas ordenadas por data de vencimento dentro de cada lista
- Clique em qualquer tarefa abre o Google Tasks no navegador
- Atualização automática a cada 5 minutos
- Tema escuro semi-transparente, posicionado à esquerda do jira-widget

## Requisitos

- Python 3.8+
- GTK 3 (`python3-gi`, `gir1.2-gtk-3.0`)
- Compositing habilitado no GNOME (para transparência)

## Instalação

### 1. Clonar / copiar o repositório

```bash
# já está em ~/src/googletasks-widget/
```

### 2. Instalar dependências Python

```bash
pip install --user -r ~/src/googletasks-widget/requirements.txt
```

### 3. Configurar o Google Cloud

> O widget guia você por esses passos através dos botões na interface.

**3.1 — Criar projeto e ativar a API**

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Crie um projeto ou selecione um existente
3. Vá em **APIs & Services → Library** e pesquise **Google Tasks API**
4. Clique em **Enable**

> Se o widget exibir o erro *"Google Tasks API has not been used in proj"*, clique no
> botão **⚡ Ativar Google Tasks API** que aparece — ele abre a página correta diretamente.

**3.2 — Criar credenciais OAuth2**

1. Vá em **APIs & Services → Credentials → Create Credentials → OAuth client ID**
2. Tipo: **Desktop app**
3. Clique em **Download JSON** e salve como `credentials.json`
4. Copie o arquivo para:

```bash
mkdir -p ~/.config/googletasks-widget
cp ~/Downloads/credentials.json ~/.config/googletasks-widget/credentials.json
```

> Se o widget exibir *"Salve o credentials.json em..."*, clique no botão
> **🌐 Abrir Google Cloud Console** — ele abre a página de credenciais diretamente.

**3.3 — Autorizar o acesso**

1. Com o `credentials.json` em lugar, reinicie o widget
2. Clique no botão **🔑 Autentique-se**
3. O navegador abrirá para autorização da conta Google
4. Após autorizar, o token é salvo em `~/.config/googletasks-widget/token.json`
   e renovado automaticamente — você não precisa fazer isso novamente

## Serviço systemd (recomendado)

O widget é gerenciado via systemd user service e inicia automaticamente no login.

```bash
# Verificar status
systemctl --user status googletasks-widget

# Reiniciar (ex: após colocar credentials.json)
systemctl --user restart googletasks-widget

# Ver logs
journalctl --user -u googletasks-widget -f

# Parar
systemctl --user stop googletasks-widget
```

## Execução manual (sem systemd)

```bash
GDK_BACKEND=x11 python3 ~/src/googletasks-widget/main.py
```

## Solução de problemas

| Sintoma | Causa | Solução |
|---|---|---|
| Botão "Salve o credentials.json" | `credentials.json` ausente | Seguir passo 3.2 acima |
| Botão "Autentique-se" | Sem token OAuth2 | Clicar no botão e autorizar no navegador |
| Erro 403 API not enabled | Google Tasks API desativada | Clicar em "⚡ Ativar Google Tasks API" |
| Tela em branco / sem janela | Problema de display | Executar com `GDK_BACKEND=x11` |
| Token expirado | Refresh falhou | Clicar em "Autentique-se" novamente |

## Estrutura

```
~/src/googletasks-widget/
├── main.py           # Widget GTK principal
├── requirements.txt  # Dependências Python
└── README.md

~/.config/googletasks-widget/
├── credentials.json  # Credenciais OAuth2 (não versionar!)
└── token.json        # Token de acesso (gerado automaticamente)

~/.config/systemd/user/
└── googletasks-widget.service  # Serviço systemd
```
