"""
Bot Discord — Aniversários

Conforme as diretrizes do Discord Developer Policy:
- Usa apenas slash commands (interactions), sem Message Content Intent
- Solicita permissões mínimas no servidor
- Armazena a data de nascimento informada pelo usuário para lembretes anuais
- Boas-vindas automáticas são opt-in (configuradas por administradores)
"""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, Union

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
APPLICATION_ID = os.getenv("APPLICATION_ID")
GUILD_ID = os.getenv("GUILD_ID")
ENABLE_WELCOME = os.getenv("ENABLE_WELCOME", "false").lower() in {"1", "true", "yes"}

CONFIG_PATH = Path(__file__).parent / "guild_config.json"
ANIVERSARIOS_PATH = Path(__file__).parent / "aniversarios.json"
PRIVACY_URL = os.getenv("PRIVACY_URL", "")
SUPPORT_URL = os.getenv("SUPPORT_URL", "")

# Permissões mínimas: Ver canais + Enviar mensagens + Incorporar links
PERMISSIONS_MINIMAS = 19456

intents = discord.Intents.default()
if ENABLE_WELCOME:
    intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned,
    intents=intents,
    description="Registra datas de nascimento e envia lembretes anuais de aniversário.",
)


def carregar_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def salvar_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")


def carregar_aniversarios() -> dict:
    if not ANIVERSARIOS_PATH.exists():
        return {}
    try:
        return json.loads(ANIVERSARIOS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def salvar_aniversarios(dados: dict) -> None:
    ANIVERSARIOS_PATH.write_text(json.dumps(dados, indent=2), encoding="utf-8")


def config_servidor(guild_id: int) -> dict:
    config = carregar_config()
    chave = str(guild_id)
    if chave not in config:
        config[chave] = {"welcome_channel_id": None, "welcome_enabled": False}
    return config[chave]


def atualizar_servidor(guild_id: int, **kwargs) -> dict:
    config = carregar_config()
    chave = str(guild_id)
    atual = config.get(chave, {"welcome_channel_id": None, "welcome_enabled": False})
    atual.update(kwargs)
    config[chave] = atual
    salvar_config(config)
    return atual


def data_aniversario_no_ano(ano: int, nascimento: date) -> date:
    try:
        return date(ano, nascimento.month, nascimento.day)
    except ValueError:
        if nascimento.month == 2 and nascimento.day == 29:
            return date(ano, 2, 28)
        raise


def calcular_proximo_aniversario(nascimento: date, hoje: Optional[date] = None) -> date:
    hoje = hoje or date.today()
    aniversario_este_ano = data_aniversario_no_ano(hoje.year, nascimento)
    if aniversario_este_ano >= hoje:
        return aniversario_este_ano
    return data_aniversario_no_ano(hoje.year + 1, nascimento)


def formatar_dias_ate_aniversario(nascimento: date) -> str:
    proximo = calcular_proximo_aniversario(nascimento)
    delta = (proximo - date.today()).days
    if delta == 0:
        return "Hoje"
    if delta == 1:
        return "amanhã"
    return f"em {delta} dias"


def obter_aniversario_usuario(guild_id: int, user_id: int) -> Optional[date]:
    dados = carregar_aniversarios()
    payload = dados.get(str(guild_id), {}).get(str(user_id))
    if not payload or not payload.get("nascimento"):
        return None
    try:
        return date.fromisoformat(payload["nascimento"])
    except ValueError:
        return None


def rodape_privacidade() -> str:
    return "Data de nascimento cadastrada por você · Lembretes anuais localmente armazenados"


def embed_aniversario(usuario: Union[discord.User, discord.Member], nascimento: date) -> discord.Embed:
    proximo = calcular_proximo_aniversario(nascimento)
    embed = discord.Embed(
        title="Aniversário cadastrado",
        description=f"Próximo aniversário de {usuario.mention} será em {proximo.strftime('%d/%m/%Y')} ({formatar_dias_ate_aniversario(nascimento)}).",
        color=discord.Color.gold(),
    )
    embed.set_author(name=str(usuario), icon_url=usuario.display_avatar.url)
    embed.add_field(name="Data de nascimento", value=nascimento.strftime("%d/%m/%Y"), inline=False)
    embed.add_field(name="Próximo aniversário", value=proximo.strftime("%d/%m/%Y"), inline=False)
    embed.set_footer(text=rodape_privacidade())
    return embed


def url_convite() -> Optional[str]:
    if not APPLICATION_ID:
        return None
    return (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={APPLICATION_ID}"
        f"&permissions={PERMISSIONS_MINIMAS}"
        f"&scope=bot%20applications.commands"
    )


def requer_guild():
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este comando só funciona em servidores.", ephemeral=True
            )
            return False
        return True

    return app_commands.check(predicate)


def requer_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Permissão insuficiente.", ephemeral=True
            )
            return False
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "Apenas administradores (`Gerenciar Servidor`) podem usar este comando.",
                ephemeral=True,
            )
            return False
        return True

    return app_commands.check(predicate)


async def verificar_aniversarios() -> None:
    await bot.wait_until_ready()
    while not bot.is_closed():
        hoje = date.today()
        dados = carregar_aniversarios()

        for guild_id_str, usuarios in dados.items():
            guild = bot.get_guild(int(guild_id_str))
            if guild is None:
                continue
            canal = guild.system_channel or next(
                (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
                None,
            )
            if canal is None:
                continue

            for usuario_id, payload in usuarios.items():
                try:
                    nascimento = date.fromisoformat(payload["nascimento"])
                except (TypeError, ValueError):
                    continue

                ultimo_ano = payload.get("ultimo_ano")
                if ultimo_ano == hoje.year:
                    continue

                if nascimento.month == hoje.month and nascimento.day == hoje.day:
                    usuario = guild.get_member(int(usuario_id)) or await bot.fetch_user(int(usuario_id))
                    mensagem = (
                        f"🎉 Hoje é aniversário de {usuario.mention if hasattr(usuario, 'mention') else usuario}!"
                        f"\nParabéns!"
                    )
                    await canal.send(mensagem)
                    payload["ultimo_ano"] = hoje.year
                    salvar_aniversarios(dados)

        await discord.utils.sleep_until(datetime.combine(hoje + timedelta(days=1), datetime.min.time()))


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="/aniversario · /ajuda",
        )
    )
    print(f"Bot conectado como {bot.user} (ID: {bot.user.id})")
    print(f"Intents: members={'sim' if ENABLE_WELCOME else 'não (padrão)'}")
    bot.loop.create_task(verificar_aniversarios())

    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        print(f"Comandos sincronizados no servidor {GUILD_ID}")
    else:
        await bot.tree.sync()
        print("Comandos sincronizados globalmente")


if ENABLE_WELCOME:

    @bot.event
    async def on_member_join(member: discord.Member):
        cfg = config_servidor(member.guild.id)
        if not cfg.get("welcome_enabled"):
            return

        canal_id = cfg.get("welcome_channel_id")
        if not canal_id:
            return

        canal = member.guild.get_channel(canal_id)
        if not isinstance(canal, discord.TextChannel):
            return
        if not canal.permissions_for(member.guild.me).send_messages:
            return

        nascimento = obter_aniversario_usuario(member.guild.id, member.id)
        if nascimento is None:
            return

        embed = embed_aniversario(member, nascimento)
        embed.title = f"Bem-vindo(a), {member.display_name}!"
        await canal.send(content=member.mention, embed=embed)


@bot.tree.command(
    name="aniversario",
    description="Registra sua data de nascimento e mostra o próximo aniversário",
)
@app_commands.describe(
    data_nascimento="Sua data de nascimento no formato AAAA-MM-DD",
    usuario="Membro para consultar (opcional)",
)
@requer_guild()
async def comando_idade(
    interaction: discord.Interaction,
    data_nascimento: Optional[str] = None,
    usuario: Optional[discord.Member] = None,
):
    alvo = usuario or interaction.user

    if data_nascimento is not None:
        try:
            nascimento = date.fromisoformat(data_nascimento)
        except ValueError:
            await interaction.response.send_message(
                "Use a data no formato AAAA-MM-DD. Exemplo: `2000-12-25`.",
                ephemeral=True,
            )
            return

        if nascimento > date.today():
            await interaction.response.send_message(
                "A data de nascimento não pode ser no futuro.",
                ephemeral=True,
            )
            return

        dados = carregar_aniversarios()
        guild_key = str(interaction.guild_id)
        guild_dados = dados.setdefault(guild_key, {})
        guild_dados[str(interaction.user.id)] = {"nascimento": nascimento.isoformat(), "ultimo_ano": None}
        salvar_aniversarios(dados)

        await interaction.response.send_message(
            embed=embed_aniversario(alvo, nascimento),
            ephemeral=True,
        )
        return

    nascimento = obter_aniversario_usuario(interaction.guild_id, alvo.id)
    if nascimento is None:
        await interaction.response.send_message(
            f"{alvo.mention} ainda não cadastrou a data de nascimento."
            if alvo.id != interaction.user.id
            else "Você ainda não cadastrou a data de nascimento. Use `/aniversario data_nascimento:AAAA-MM-DD`.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(embed=embed_aniversario(alvo, nascimento), ephemeral=True)


@bot.tree.command(
    name="verificar-participantes",
    description="Lista os aniversários dos membros no seu canal de voz",
)
@requer_guild()
async def verificar_participantes(interaction: discord.Interaction):
    membro = interaction.user
    assert isinstance(membro, discord.Member)

    if not membro.voice or not membro.voice.channel:
        await interaction.response.send_message(
            "Entre em um canal de voz para usar este comando.", ephemeral=True
        )
        return

    canal_voz = membro.voice.channel
    participantes = [m for m in canal_voz.members if not m.bot]

    if not participantes:
        await interaction.response.send_message(
            "Não há participantes humanos no canal de voz.", ephemeral=True
        )
        return

    linhas = []
    for p in sorted(participantes, key=lambda x: x.display_name.lower()):
        nascimento = obter_aniversario_usuario(interaction.guild_id, p.id)
        if nascimento is None:
            linhas.append(f"{p.mention} — sem data de nascimento")
            continue
        linhas.append(
            f"{p.mention} — {nascimento.strftime('%d/%m')} ({formatar_dias_ate_aniversario(nascimento)})"
        )

    embed = discord.Embed(
        title=f"Canal de voz: {canal_voz.name}",
        description="\n".join(linhas[:25]),
        color=discord.Color.green(),
    )
    if len(participantes) > 25:
        embed.set_footer(text=f"Mostrando 25 de {len(participantes)} participantes")
    else:
        embed.set_footer(text=rodape_privacidade())

    await interaction.response.send_message(embed=embed, ephemeral=True)


config_group = app_commands.Group(
    name="config",
    description="Configurações do servidor (apenas administradores)",
    default_permissions=discord.Permissions(manage_guild=True),
)


@config_group.command(
    name="boas-vindas",
    description="Ativa ou desativa mensagem de boas-vindas com idade da conta",
)
@app_commands.describe(
    canal="Canal onde enviar boas-vindas (deixe vazio para desativar)",
    ativar="Ligar ou desligar as boas-vindas automáticas",
)
@requer_guild()
@requer_admin()
async def config_boas_vindas(
    interaction: discord.Interaction,
    ativar: bool,
    canal: Optional[discord.TextChannel] = None,
):
    if ativar and canal is None:
        await interaction.response.send_message(
            "Informe o canal ao ativar as boas-vindas.", ephemeral=True
        )
        return

    if not ENABLE_WELCOME:
        await interaction.response.send_message(
            "Boas-vindas automáticas não estão habilitadas na hospedagem do bot.\n"
            "O operador deve definir `ENABLE_WELCOME=true` e ativar "
            "**Server Members Intent** no [Developer Portal](https://discord.com/developers/applications).",
            ephemeral=True,
        )
        return

    if ativar and canal and not canal.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message(
            f"Não tenho permissão para enviar mensagens em {canal.mention}.",
            ephemeral=True,
        )
        return

    atualizar_servidor(
        interaction.guild.id,
        welcome_enabled=ativar,
        welcome_channel_id=canal.id if ativar and canal else None,
    )

    if ativar:
        texto = f"Boas-vindas ativadas em {canal.mention}."
    else:
        texto = "Boas-vindas automáticas desativadas."

    await interaction.response.send_message(texto, ephemeral=True)


bot.tree.add_command(config_group)


@bot.tree.command(name="ajuda", description="Explica o bot, permissões e conformidade com o Discord")
async def comando_ajuda(interaction: discord.Interaction):
    convite = url_convite()
    permissoes = (
        "• Ver canais\n"
        "• Enviar mensagens\n"
        "• Incorporar links\n"
        "• Comandos de aplicativo (`applications.commands`)"
    )

    embed = discord.Embed(
        title="Idade da Conta — Ajuda",
        description=(
            "Bot utilitário que mostra **há quanto tempo uma conta Discord existe**, "
            "usando dados públicos da API (campo `created_at`)."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Comandos",
        value=(
            "`/aniversario` — consulta idade da conta\n"
            "`/verificar-participantes` — canal de voz atual\n"
            "`/config boas-vindas` — boas-vindas (admin)\n"
            "`/privacidade` — política de dados\n"
            "`/convite` — link de adição ao servidor"
        ),
        inline=False,
    )
    embed.add_field(name="Permissões solicitadas", value=permissoes, inline=False)
    embed.add_field(
        name="Conformidade Discord",
        value=(
            "• Apenas slash commands (sem leitura de mensagens)\n"
            "• Sem armazenamento de dados pessoais\n"
            "• Respostas efêmeras por padrão (privacidade)\n"
            "• Boas-vindas opt-in, configuradas por admins"
        ),
        inline=False,
    )
    if convite:
        embed.add_field(name="Adicionar a outro servidor", value=convite, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="privacidade", description="Política de privacidade e uso de dados")
async def comando_privacidade(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Política de Privacidade",
        color=discord.Color.dark_grey(),
    )
    embed.description = (
        "**Dados utilizados:** apenas o identificador público do usuário e a data de "
        "criação da conta (`created_at`), fornecidos pela API oficial do Discord.\n\n"
        "**Não coletamos:** idade real, e-mail, IP, conteúdo de mensagens ou histórico.\n\n"
        "**Armazenamento:** o bot não persiste dados de usuários. Apenas configurações "
        "do servidor (canal de boas-vindas) são salvas localmente.\n\n"
        "**Finalidade:** exibir informação solicitada via comando ou boas-vindas "
        "autorizadas pelo administrador do servidor."
    )
    if PRIVACY_URL:
        embed.add_field(name="Política completa", value=PRIVACY_URL, inline=False)
    if SUPPORT_URL:
        embed.add_field(name="Suporte / reportar problemas", value=SUPPORT_URL, inline=False)

    embed.set_footer(text="Em conformidade com a Discord Developer Policy")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="convite", description="Gera o link oficial para adicionar o bot ao servidor")
async def comando_convite(interaction: discord.Interaction):
    convite = url_convite()
    if not convite:
        await interaction.response.send_message(
            "Link não configurado. Defina `APPLICATION_ID` no ambiente do bot.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title="Adicionar bot ao servidor",
        description=(
            f"[Clique aqui para convidar o bot]({convite})\n\n"
            "Requisitos para quem adiciona: permissão **Gerenciar Servidor**.\n"
            "O bot solicita apenas permissões mínimas necessárias."
        ),
        color=discord.Color.green(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@comando_idade.error
@verificar_participantes.error
async def cooldown_handler(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Aguarde {error.retry_after:.0f}s antes de usar novamente.",
            ephemeral=True,
        )


def main():
    if not TOKEN:
        raise SystemExit(
            "Defina DISCORD_TOKEN no arquivo .env\n"
            "Copie .env.example para .env e preencha as variáveis."
        )
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
