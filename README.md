# Bot Discord — Idade da Conta

Bot utilitário em conformidade com as [diretrizes de desenvolvedores do Discord](https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy). Mostra **há quanto tempo a conta Discord existe** — não a idade real da pessoa.

## Por que é fácil integrar em servidores

| Prática | Benefício |
|---------|-----------|
| Apenas **slash commands** | Sem Message Content Intent — aprovação mais simples |
| **Permissões mínimas** | Admins confiam mais ao convidar |
| Respostas **efêmeras** | Menos spam no chat, mais privacidade |
| Boas-vindas **opt-in** | Admin decide canal e ativação |
| `/convite` integrado | Link OAuth2 correto com um comando |
| `PRIVACY.md` incluído | Requisito para bots verificados (+100 servidores) |

## Permissões solicitadas

```
Ver canais · Enviar mensagens · Incorporar links · applications.commands
```

Valor numérico para OAuth2: `19456`

Link de convite (substitua `SEU_APPLICATION_ID`):

```
https://discord.com/oauth2/authorize?client_id=SEU_APPLICATION_ID&permissions=19456&scope=bot%20applications.commands
```

## Comandos

| Comando | Quem pode usar | Descrição |
|---------|----------------|-----------|
| `/idade` | Todos | Idade da conta (resposta privada) |
| `/verificar-participantes` | Todos | Idades no canal de voz atual |
| `/config boas-vindas` | Admin | Ativa/desativa boas-vindas |
| `/ajuda` | Todos | Documentação e conformidade |
| `/privacidade` | Todos | Política de dados |
| `/convite` | Todos | Link para adicionar o bot |

## Configuração no Developer Portal

### 1. Criar aplicação

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. **General Information** → copie o **Application ID**
3. **Bot** → **Reset Token** → copie o token

### 2. Intents (importante)

| Intent | Quando usar |
|--------|-------------|
| **Server Members Intent** | Só se `ENABLE_WELCOME=true` (boas-vindas automáticas) |
| **Message Content Intent** | **Não ativar** — o bot não lê mensagens |

### 3. Installation (recomendado)

Em **Installation**:

- **Guild Install**: ativado (bot para servidores)
- **User Install**: desativado (não necessário)
- Scopes: `bot`, `applications.commands`

### 4. OAuth2 URL Generator

- Scopes: `bot`, `applications.commands`
- Permissões: View Channels, Send Messages, Embed Links

### 5. Verificação (+100 servidores)

Para escalar, prepare:

- [ ] Política de privacidade pública (`PRIVACY.md` hospedado em URL)
- [ ] Canal de suporte (`SUPPORT_URL`)
- [ ] Descrição clara do bot no portal
- [ ] Justificativa do Server Members Intent (se usado): *"Enviar mensagem de boas-vindas quando configurado pelo admin"*

## Instalação local

```bash
cd discord-bot-idade
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edite .env com DISCORD_TOKEN e APPLICATION_ID
python bot.py
```

## Variáveis de ambiente

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `DISCORD_TOKEN` | Sim | Token do bot |
| `APPLICATION_ID` | Recomendado | ID da aplicação (link `/convite`) |
| `GUILD_ID` | Não | Servidor de testes (sync rápido) |
| `ENABLE_WELCOME` | Não | `true` para boas-vindas automáticas |
| `PRIVACY_URL` | Não | URL pública da política de privacidade |
| `SUPPORT_URL` | Não | Discord/GitHub para suporte |

## Fluxo de integração no servidor

1. Admin com **Gerenciar Servidor** usa o link de convite
2. Bot entra com permissões mínimas
3. Membros usam `/idade` (resposta só para quem executou)
4. *(Opcional)* Admin executa `/config boas-vindas ativar:#canal`

## Limitação

O Discord **não expõe idade real** via API. Este bot mostra apenas a **idade da conta** (data de criação derivada do snowflake ID).
