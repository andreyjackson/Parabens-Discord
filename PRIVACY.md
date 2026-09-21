# Política de Privacidade — Bot Idade da Conta

**Última atualização:** junho de 2026

## Resumo

Este bot do Discord exibe **há quanto tempo uma conta Discord existe**. Não coleta, vende nem compartilha dados pessoais dos usuários.

## Dados utilizados

| Dado | Origem | Uso |
|------|--------|-----|
| ID do usuário | API oficial do Discord | Identificar o membro consultado |
| Data de criação da conta (`created_at`) | API oficial do Discord | Calcular idade da conta |
| Configuração do servidor | Administrador do servidor | Canal de boas-vindas (opcional) |

## Dados que NÃO utilizamos

- Idade real ou data de nascimento
- Conteúdo de mensagens
- Endereço de e-mail ou IP
- Dados de localização
- Histórico de conversas

## Armazenamento

- **Usuários:** nenhum dado é persistido em banco de dados.
- **Servidores:** apenas preferências locais (canal de boas-vindas ativo/inativo) em `guild_config.json` na máquina que hospeda o bot.

## Base legal e finalidade

Os dados são usados exclusivamente para responder a comandos slash solicitados pelo usuário ou enviar mensagens de boas-vindas quando **explicitamente configuradas** por um administrador do servidor.

## Conformidade com o Discord

Este bot segue a [Discord Developer Policy](https://support-dev.discord.com/hc/en-us/articles/8563934450327-Discord-Developer-Policy) e utiliza:

- Slash commands (interactions) em vez de leitura de mensagens
- Permissões mínimas no servidor
- Server Members Intent apenas quando boas-vindas automáticas estão habilitadas pelo operador

## Contato

Configure `SUPPORT_URL` no ambiente do bot ou abra uma issue no repositório do projeto para reportar problemas.
