import discord
import requests
from discord.ext import commands
from discord import app_commands
import json
import os
import random
import asyncio

intents = discord.Intents.all()
NEKOBOT_API_URL = 'https://nekobot.xyz/api/imagegen?type=changemymind'


bot = commands.Bot(command_prefix='/', intents=intents)
tree = bot.tree

# Kullanıcı bakiyeleri
user_balances = {}

cooldowns = {}

# JSON'dan verileri yükleme ve kaydetme işlevi
def load_data():
    if os.path.exists('selected_channel.json'):
        with open('selected_channel.json', 'r') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open('selected_channel.json', 'w') as file:
        json.dump(data, file)

selected_channel_id = load_data().get("selected_channel_id", None)

kelime_listesi = {
    "Programlama Dilleri": ["python", "java", "javascript", "csharp", "ruby", "c", "c++", "go", "swift", "kotlin", "php", "typescript", "r", "objective-c", "perl", "scala", "haskell", "rust", "dart", "matlab", "lua", "clojure", "elixir", "f#", "groovy", "visual basic", "assembly", "fortran", "cobol", "sas"],
    "Hayvanlar": ["kedi", "köpek", "fil", "zürafa", "aslan", "maymun", "kurbağa", "timsah", "panda", "zürafa", "kanguru", "kuş", "balina", "yılan", "kaplan", "ayı", "geyik", "çita", "penguen", "yılan", "çakal", "papağan", "sincap", "kertenkele", "kartal", "yılan", "örümcek", "tavşan", "su samuru", "zebra"],
    "Ülkeler": ["türkiye", "brezilya", "kanada", "almanya", "japonya", "amerika birleşik devletleri", "fransa", "italya", "ispanya", "çin", "hindistan", "rusya", "avustralya", "birleşik krallık", "meksika", "güney kore", "arjantin", "endonezya", "güney afrika", "suudi arabistan", "isveç", "norveç", "finlandiya", "isviçre", "polonya", "hollanda", "belçika", "avusturya", "danimarka", "yunanistan", "portekiz", "yeni zelanda", "irlanda", "singapur", "malezya"],
    "Meyveler": ["elma", "muz", "kiraz", "hurma", "çilek", "armut", "mandalina", "portakal", "turunç", "kumkat", "ayva", "kivi", "üzüm", "erik", "incir", "alıç", "karadut", "dut", "frambuaz", "kavun", "karpuz", "şeftali", "yaban mersini", "kuşburnu"],
    "Tropikal Meyveler": ["ananas", "avokado", "mango", "hindistan cevizi", "papaya", "pomelo", "hurma", "yıldız meyvesi", "pitaya", "çarkıfelek", "liçi"]
}

# Adam asmaca oyun durumu
adam_asmaca_durumu = {}

@bot.event
async def on_ready():
    global selected_channel_id
    selected_channel_id = load_data().get("selected_channel_id", None)
    print(f'Bot {bot.user} olarak giriş yaptı.')
    print(f'Seçilen kanal ID: {selected_channel_id}')
    await tree.sync()  # Komut ağacımızı senkronize ediyoruz

@tree.command(name='değiştir', description="Komutların çalışabileceği kanalı belirler")
async def degistir(interaction: discord.Interaction, kanal: discord.TextChannel):
    global selected_channel_id
    selected_channel_id = kanal.id
    save_data({"selected_channel_id": selected_channel_id})
    await interaction.response.send_message(f'{interaction.user.mention}, komutlar bundan böyle sadece `{kanal}` kanalından çalışacaktır.')


@bot.event
async def on_message(message):
    global selected_channel_id

    if message.author == bot.user:
        return

    if selected_channel_id and message.channel.id != selected_channel_id and message.content.startswith('/'):
        try:
            await message.delete()
            await message.author.send(f'{message.author.mention}, komutları yalnızca <#{selected_channel_id}> kanalında kullanabilirsiniz.')
        except discord.Forbidden:
            pass  # Handle cases where the bot doesn't have permissions to delete messages or send DMs

    await bot.process_commands(message)
    # Ek olarak, istenmeyen mesajları silmek için şunu kullanabilirsiniz:
    if selected_channel_id and message.channel.id != selected_channel_id and message.content.startswith('/'):
        try:
            await message.delete()
        except discord.Forbidden:
            pass
            
        
    elif message.channel.id == selected_channel_id and message.author in adam_asmaca_durumu:
        user = message.author
        kelime_durumu = adam_asmaca_durumu[user]
        kelime = kelime_durumu["kelime"]

        if message.content.lower() in kelime:
            for idx, harf in enumerate(kelime):
                if harf == message.content.lower():
                    kelime_durumu["bulunan_harfler"][idx] = harf
            await message.channel.send(embed=adam_asmaca_mesaji(user))
            
            if "_" not in kelime_durumu["bulunan_harfler"]:
                user_balances[user] += 200
                await message.channel.send(embed=adam_asmaca_dogru_mesaji(user))
                del adam_asmaca_durumu[user]
        else:
            if message.content.lower() not in kelime_durumu["yanlis_harfler"]:
                kelime_durumu["yanlis_harfler"].append(message.content.lower())
                kelime_durumu["cizim"] += 1
                await message.channel.send(embed=adam_asmaca_mesaji(user))
                
                if kelime_durumu["cizim"] == 6:
                    await message.channel.send(f'{user.mention}, kaybettiniz! Doğru kelime `{kelime}` idi.')
                    del adam_asmaca_durumu[user]

    await bot.process_commands(message)

@tree.command(name='cash', description="Hesap bakiyenizi kontrol edin")
async def check_cash(interaction: discord.Interaction):
    user = interaction.user
    if user not in user_balances:
        user_balances[user] = 10000
    
    await interaction.response.send_message(f'{user.mention}, senin bakiyen: {user_balances[user]} cash.')

@tree.command(name='coin', description="Bahis ile yazı tura atın")
@app_commands.checks.cooldown(rate=1, per=10)
async def coin_flip(interaction: discord.Interaction, amount: int):
    user = interaction.user

    # Bahis miktarını kontrol et
    amount = abs(amount)
    if amount < 500:
        await interaction.response.send_message('En az 500 cash ile oynamalısın.')
        return
    if user not in user_balances or user_balances[user] < amount:
        await interaction.response.send_message(f'Yeterli paraya sahip değilsin, senin bakiyen: {user_balances.get(user, 0)} cash.')
        return

    # Animasyon mesajını gönder ve referansını sakla
    flip_message = await interaction.response.send_message('Starting...')
    await asyncio.sleep(0.1)

    # Para atma animasyonu (Bu kısım opsional, detaylı animasyon için kullanılır)
    for _ in range(2):
        await interaction.edit_original_response(content='<:yaz:1254863097894801511>')
        await asyncio.sleep(0.3)
        await interaction.edit_original_response(content='<:tura:1254863027694731414>')
        await asyncio.sleep(0.3)

    coin = random.choice(['Yazi', 'Tura'])
    if coin == 'Yazi':
        user_balances[user] += amount
        result = f'{user.mention}, sonuç: <:yaz:1254863097894801511> Yazı! Parayı İkiye katladın: {user_balances[user]} cash\'ın var artık.'
    else:
        user_balances[user] -= amount
        result = f'{user.mention}, sonuç: <:tura:1254863027694731414> Tura, Kaybettin!,  Güncel bakiyen: {user_balances[user]} cash.'

    # Sonuç mesajını gönder ve devamı için yanıt bekle
    await interaction.edit_original_response(content=result)
    
@tree.command(name='add', description="Kullanıcı bakiyesine cash ekleyin")
@app_commands.checks.has_permissions(administrator=True)
async def add_cash(interaction: discord.Interaction, member: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Yanlış komut, örn: /add {username} {amount}")
        return
    if member not in user_balances:
        user_balances[member] = 0
    user_balances[member] += amount
    await interaction.response.send_message(f'{member.mention}, hesabına {amount} cash eklendi. Yeni bakiye: {user_balances[member]} cash.')

@tree.command(name='remove', description="Kullanıcı bakiyesinden cash çıkarın")
@app_commands.checks.has_permissions(administrator=True)
async def remove_cash(interaction: discord.Interaction, member: discord.Member, amount: int):
    if amount <= 0:
        await interaction.response.send_message("Yanlış komut, örn: /remove {username} {amount}")
        return
    if member not in user_balances or user_balances[member] < amount:
        await interaction.response.send_message(f'{member.mention}, yeterli bakiye yok. İşlem iptal edildi.')
        return
    user_balances[member] -= amount
    await interaction.response.send_message(f'{member.mention}, hesabından {amount} cash düşürüldü. Yeni bakiye: {user_balances[member]} cash.')
    
@tree.command(name='adam_asmaca', description="Adam asmaca oyununu başlatın")
async def adam_asmaca(interaction: discord.Interaction):
    user = interaction.user
    if user in adam_asmaca_durumu:
        await interaction.response.send_message(f'{user.mention}, zaten bir adam asmaca oyununuz var.')
        return

    kategori = random.choice(list(kelime_listesi.keys()))
    kelime = random.choice(kelime_listesi[kategori])
    bulunan_harfler = ["_" if c != ' ' else ' ' for c in kelime]
    adam_asmaca_durumu[user] = {
        "kelime": kelime,
        "kategori": kategori,
        "bulunan_harfler": bulunan_harfler,
        "yanlis_harfler": [],
        "cizim": 0
    }

    await interaction.response.send_message(embed=adam_asmaca_mesaji(user))

@bot.event
async def on_message(message):
    user = message.author
    if user == bot.user:
        return

    if user in adam_asmaca_durumu:
        harf = message.content.lower()
        if len(harf) == 1 and harf.isalpha():
            kelime_durumu = adam_asmaca_durumu[user]
            kelime = kelime_durumu["kelime"]

            if harf in kelime_durumu["bulunan_harfler"] or harf in kelime_durumu["yanlis_harfler"]:
                await message.channel.send(f'{user.mention}, bu harfi zaten tahmin ettiniz.')
                return

            if harf in kelime:
                for i, c in enumerate(kelime):
                    if c == harf:
                        kelime_durumu["bulunan_harfler"][i] = harf
                if "_" not in kelime_durumu["bulunan_harfler"]:
                    if user not in user_balances:
                        user_balances[user] = 10000  # Kullanıcının başlangıç bakiyesi
                    user_balances[user] += 200  # Kullanıcıya 200 cash ekle
                    await message.channel.send(embed=adam_asmaca_dogru_mesaji(user))
                    del adam_asmaca_durumu[user]
                else:
                    await message.channel.send(embed=adam_asmaca_mesaji(user))
            else:
                kelime_durumu["yanlis_harfler"].append(harf)
                kelime_durumu["cizim"] += 1
                if kelime_durumu["cizim"] >= 5:
                    await message.channel.send(f'{user.mention}, kaybettiniz. Kelime: {kelime}')
                    del adam_asmaca_durumu[user]
                else:
                    await message.channel.send(f'{user.mention}, yanlış harf!')
                    await message.channel.send(embed=adam_asmaca_mesaji(user))

    await bot.process_commands(message)

def adam_asmaca_mesaji(user):
    kelime_durumu = adam_asmaca_durumu[user]
    kelime = " ".join(kelime_durumu["bulunan_harfler"])
    yanlis_harfler = ", ".join(kelime_durumu["yanlis_harfler"]) if kelime_durumu["yanlis_harfler"] else "Yok"

    kategori = kelime_durumu["kategori"]

    asci_art = [
        "```\n_________\n|    |\n|    \n|    \n|    \n|\n```",
        "```\n_________\n|    |\n|    😵\n|    \n|    \n|\n```",
        "```\n_________\n|    |\n|    😵\n|    ()\n|    \n|\n```",
        "```\n_________\n|    |\n|    😵\n|   ┌()\n|    \n|\n```",
        "```\n_________\n|    |\n|    😵\n|   ┌()┐\n|    \n|\n```",
        "```\n_________\n|    |\n|    😵\n|   ┌()┐\n|    /\n|\n```",
        "```\n_________\n|    |\n|    😵\n|   ┌()┐\n|    / \\\n|\n```"
    ]

    embed = discord.Embed(title="Adam Asmaca", description=f"**Kategori:** {kategori}\n**Kelime:**    `{kelime}`\n**Yanlış Harfler:** {yanlis_harfler}")
    embed.add_field(name="Adam", value=asci_art[kelime_durumu["cizim"]], inline=False)
    return embed

def adam_asmaca_dogru_mesaji(user):
    kelime_durumu = adam_asmaca_durumu[user]
    kelime = " ".join(kelime_durumu["bulunan_harfler"]).replace(" ", " ")
    yanlis_harfler = ", ".join(kelime_durumu["yanlis_harfler"]) if kelime_durumu["yanlis_harfler"] else "Yok"
    cizim = kelime_durumu["cizim"]
    kategori = kelime_durumu["kategori"]

    asci_art = [
        "_________\n|    |\n|    \n|    \n|    \n|\n",
        "_________\n|    |\n|    😵\n|    \n|    \n|\n",
        "_________\n|    |\n|    😵\n|    ()\n|    \n|\n",
        "_________\n|    |\n|    😵\n|   ┌()\n|    \n|\n",
        "_________\n|    |\n|    😵\n|   ┌()┐\n|    \n|\n",
        "_________\n|    |\n|    😵\n|   ┌()┐\n|    /\n|\n"
    ]

    embed = discord.Embed(title="Adam Asmaca", description=f"**Doğru Bildin!** 200 cash kazandın! Yeni bakiyen: {user_balances[user]} cash\n**Kategori:** {kategori}\n**Kelime:**    `{kelime}`\n**Yanlış Harfler:** {yanlis_harfler}")
    embed.add_field(name="Adam", value=f"```\n{asci_art[cizim]}```", inline=False)
    return embed
    
@tree.command(name='geliş', description="Gönderilen mesaja geliş gif'i ekler")
async def alkis(interaction: discord.Interaction, title: str):
    embed = discord.Embed(
        title=f"> **`{title}`**",
        description="",
        color=discord.Color.blue()
    )
    embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNml3NWVoeXg1OXhrM2Nwazdncm5maXB1cmY3NnVjb2lqNW82YnpsZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ymZHH7Nw0UgMjOy6ID/giphy.gif")
    await interaction.response.send_message(embed=embed)
    
    
@tree.command(name='sus', description="sus")
async def alkis(interaction: discord.Interaction ):
    embed = discord.Embed(
        description="",
        color=discord.Color.dark_theme()
    )
    embed.set_image(url="https://r.resimlink.com/yTpgSxsO4.jpg")
    await interaction.response.send_message(embed=embed)
    
    
@tree.command(name='dassak', description="ramiz")
async def alkis(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"**Cr: @4r1f_07**",
        description="",
        color=discord.Color.dark_theme()
    )
    embed.set_image(url="https://r.resimlink.com/BJgwn4pcFrv.webp")
    await interaction.response.send_message(embed=embed)
    

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    await tree.sync()  # Komut ağacını senkronize etmek

@tree.command(name="foto", description="Kullanıcının profil fotoğrafını gösterir.")
async def foto(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(color=0x00BFFF) 
    embed.set_author(name=f'{member}', icon_url=member.avatar.url)
    embed.set_image(url=member.avatar.url)
    embed.set_footer(text=f'Kullanıcının profil fotoğrafı: {member}')
    await interaction.response.send_message(embed=embed)

@tree.command(name='catsxd', description="idk")
async def alkis(interaction: discord.Interaction):
    # İki veya daha fazla resim URL'sini liste olarak belirtin
    image_urls = [
        "https://i.ibb.co/F6gsCwr/1efac4dd-d7c0-4e3d-8327-e78685278a3b.jpg",
        "https://i.ibb.co/6PjQF8s/6fbd2be3-27bb-4509-90d1-28f2c9af8915.jpg",
        "https://i.ibb.co/d2S6NMG/MISANTHROPE-CHERRY-58.gif",
        "https://i.ibb.co/6PjQF8s/6fbd2be3-27bb-4509-90d1-28f2c9af8915.jpg",
        "https://i.ibb.co/RbQcTPS/75b3605a-951b-4d30-9b26-4ff362abb287.jpg",
        "https://i.ibb.co/2MrGcWc/aeeda01e-adb5-4f17-9701-19510acce72b.jpg"
    ]

    # Rastgele bir resim URL'si seçin
    selected_image = random.choice(image_urls)

    embed = discord.Embed(
        description="",
        color=discord.Color.purple()
    )
    embed.set_image(url=selected_image)
    await interaction.response.send_message(embed=embed)
    
    
@tree.command(name='cmm', description="Generates a 'Change My Mind' meme with the specified text")
@app_commands.describe(text='The text to change my mind with')
async def changemymind(interaction: discord.Interaction, text: str):
    params = {'text': text}
    try:
        response = requests.get(NEKOBOT_API_URL, params=params)
        data = response.json()
        if response.status_code == 200:
            image_url = data['message']
            embed = discord.Embed(title="Change My Mind", color=discord.Color.dark_theme())
            embed.set_image(url=image_url)

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Error: {data['message']}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error occurred: {str(e)}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f'{bot.user} is connected to Discord!')
  
TOKEN = 'MTI1NDg1MTYzNzE3Mjg5NTk0NQ.G1REyW.0mZC6zOALBFCHLDc6-YUQEdI8UcHbTAl8YgCxQ'
bot.run(TOKEN)