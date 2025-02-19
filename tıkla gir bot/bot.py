import discord
import wikipedia
from discord.ext import commands
from config import *
import random
import pymongo
from discord import ui
from discord.ui import View, Button
from datetime import timedelta, datetime
from discord.ext.commands import MissingPermissions
import asyncio
from discord.utils import find

intents = discord.Intents.all()
intents.message_content = True

client = pymongo.MongoClient(url)
db = client.socruel

bot = commands.Bot(command_prefix=".", intents=intents)


class Modal(ui.Modal, title="So Cruel"):
    ad = ui.TextInput(label="Adınız", placeholder="Ali...", style=discord.TextStyle.short)
    öneri = ui.TextInput(label="Öneriniz", placeholder="blablalba....", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(modal_log)
        embed = discord.Embed(
            title="Yeni Öneri",
            description=f"{interaction.user}({interaction.user.id}), ``{self.ad}`` yeni bir öneride bulundu\nBulunduğu öneri: {self.öneri}",
            colour=discord.Colour.green()
        )
        await log_channel.send(embed=embed)
        await interaction.response.send_message("Yazdıkların başarıyla kaydedildi ve yetkililere gönderildi")


@bot.tree.command(name="sunmary", description="Returns a Wikipedia summary")
async def sunmary(ctx: discord.Interaction, search: str):
    await ctx.response.defer()  # Komutun işlendiğini belirt
    try:
        thesunmary = wikipedia.summary(search, chars=1950)
        await ctx.followup.send(thesunmary)
    except wikipedia.exceptions.PageError:
        searchsunmary = str(wikipedia.search(search, suggestion=True)).replace('(', '').replace(')', '').replace("'", "").replace('[', '').replace(']', '')
        await ctx.followup.send(f"I can't seem to find a summary for that.. Did you mean: {searchsunmary}")
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {e}")


@bot.tree.command(name="search", description="Serch Wikipedia")
async def search(ctx: discord.Interaction, search: str):
    await ctx.response.defer()  # Komutun işlendiğini belirt
    searchsearch = str(wikipedia.search(search, suggestion=True)).replace('(', '').replace(')', '').replace("'", "").replace('[', '').replace(']', '')
    await ctx.followup.send(searchsearch)


@bot.tree.command(name="url", description="Get a URl to a page on Wikipedia")
async def url(ctx: discord.Interaction, search: str):
    await ctx.response.defer()  # Komutun işlendiğini belirt
    try:
        urlsummary = wikipedia.summary(search, auto_suggest=False)
        search = search.lower().replace(' ', '_').replace('  ', '_')
        await ctx.followup.send(f"https://en.wikipedia.org/wiki/{search}")
    except wikipedia.exceptions.PageError:
        urlsearch = str(wikipedia.search(search, suggestion=True)).replace('(', '').replace(')', '').replace("'", "").replace('[', '').replace(']', '')
        await ctx.followup.send(f"I can't seem to find a summary for that.. Did you mean: {urlsearch}")
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {e}")


@bot.tree.command(name="random", description="Returns a random Wikipedia article")
async def random(ctx: discord.Interaction):
    await ctx.response.defer()  # Komutun işlendiğini belirt
    try:
        randomtitle = wikipedia.random()
        randomsummary = wikipedia.summary(randomtitle, chars=1950)
        link = randomtitle.replace(' ', '_')
        await ctx.followup.send(f"**{randomtitle}** \n\n{randomsummary}\n\nhttps://en.wikipedia.org/wiki/{link}")
    except Exception as e:
        await ctx.followup.send(f"An error occurred: {e}")


@bot.tree.command(name="modal", description="Modal deneme komudu")
async def modal(interaction: discord.Interaction):
    await interaction.response.send_modal(Modal())


@bot.tree.command(name="zarat", description="1-6 arası bir sayı çıkartır")
async def zarat(interaction: discord.Interaction):
    sayi = random.randint(1, 6)
    await interaction.response.send_message(f"Çıkan sayı: {sayi}")


@bot.tree.command(name="data", description="DataBase için deneme komudu")
async def data(interaction: discord.Interaction, veri: str):
    await interaction.response.send_message(f"Dataya yeni bir veri eklendi\nEklenen veri: {veri}")
    db.data.insert_one(
        {
            "veri": veri,
            "yetkili": interaction.user.id,
        }
    )


@bot.tree.command(name="work", description="Checks to see if I am online")
async def work(interaction: discord.Interaction):
    await interaction.response.send_message(f"I am working! \n\nLatency: {bot.latency * 1000:.2f} ms.")


@bot.tree.command(name="rolal", description="Tıklayıp Rol alma komutu")
async def rolal(interaction: discord.Interaction):
    class RolAlButton(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Tıkla Al", style=discord.ButtonStyle.blurple, custom_id="Tikla_1", emoji="✅")

        async def callback(self, interaction: discord.Interaction):
            uye_rol = interaction.guild.get_role(yeni_üye)
            kayitsiz_rol = interaction.guild.get_role(kayitsiz_roll)

            if uye_rol is None or kayitsiz_rol is None:
                await interaction.response.send_message("Roller bulunamadı! Lütfen bot sahibine başvurun.", ephemeral=True)
                return

            try:
                await interaction.user.add_roles(uye_rol)
                await interaction.user.remove_roles(kayitsiz_rol)
                await interaction.response.send_message(f"{uye_rol.mention} rolü verildi ve {kayitsiz_rol.mention} rolü alındı!", ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.response.send_message("Bu rolleri yönetmek için yeterli yetkim yok! Lütfen bot sahibine başvurun.", ephemeral=True)
            except Exception as e:
                print(f"Hata oluştu: {e}")
                await interaction.response.send_message("Bir hata oluştu! Lütfen tekrar deneyin veya bot sahibine başvurun.", ephemeral=True)

    view = View(timeout=None)
    view.add_item(RolAlButton())

    button_embed = discord.Embed(
        title="Rol Alma Butonu",
        description="Aşağıdaki butona tıklayarak sunucuya özel rolü alabilirsiniz.",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=button_embed, view=view)


@bot.tree.command(name="sorgu", description="DataBase içerisinde veri aramanıza yardımcı olur")
async def sorgu(interaction: discord.Interaction, veri: str):
    hex = {"veri": veri}
    if db.data.count_documents(hex) > 0:
        veri_list = db.data.find(hex)
        for i in veri_list:
            yt_info = i["yetkili"]
        await interaction.response.send_message(f"veriyi dataya ekleyen yetkili id: {yt_info}")
    elif db.data.count_documents(hex) == 0:
        await interaction.response.send_message(f"Database içerisinde ``{veri}`` adında bi veri bulanamadı")


@bot.tree.command(name="sil", description="Girdiğiniz veriyi database'den siler")
async def sil(interaction: discord.Interaction, veri: str):
    hex = {"veri": veri}
    if db.data.count_documents(hex) == 0:
        await interaction.response.send_message(f"Database içinde {veri} adında bir veri bulunamadı!")
    elif db.data.count_documents(hex) > 0:
        db.data.delete_one(hex)
        await interaction.response.send_message(f"database içindeki ``{veri}`` verisi {interaction.user.name} tarafından silinmiştir.")


@bot.tree.command(name="kick", description="etiketleyeceğiniz üyeyi sunucudan kickler.")
async def kick(interaction: discord.Integration, member: discord.Member, sebep: str):
    role = member.guild.get_role(admin)
    log_channel = bot.get_channel(ban_kick_log)
    if role in interaction.user.roles:
        kickEmbed = discord.Embed(
            title="Bir üye atıldı",
            description=f"- atılan üye: ``{member}``\n- atılan üye id: ``{member.id}``\n- atılma sebebi: ``{sebep}``\n- atan yetkili: ``{interaction.user}``\n- atan yetkili id: ``{interaction.user.id}``",
            color=discord.Colour.red()
        )
        kickEmbed.set_image(url="https://cdn.discordapp.com/avatars/348850663486259201/daeb0c95dff8562ed368a0aab73c9981.webp?size=1024&format=webp&width=563&height=563")
        await member.kick()
        await interaction.response.send_message(f"{member}({member.id}) üyesi {interaction.user}({interaction.user.id}) tarafından sunucudan kicklendi!")
        await log_channel.send(embed=kickEmbed)
    else:
        await interaction.response.send_message(f"{member}({member.id}) bu komutu kullanmaya yetkin yetmiyor!")


@bot.tree.command(name="ban", description="etiketleyeceğiniz üyeyi sunucudan yasaklar.")
async def ban(interaction: discord.Integration, member: discord.Member, sebep: str):
    role = member.guild.get_role(admin)
    log_channel = bot.get_channel(ban_kick_log)
    if role in interaction.user.roles:
        banEmbed = discord.Embed(
            title="Bir üye yasaklanadı",
            description=f"- Yasaklanan üye: ``{member}``\n- Yasaklanan üye id: ``{member.id}``\n- Yasaklanma sebebi: ``{sebep}``\n- Yasaklayan yetkili: ``{interaction.user}``\n- Yasaklayan yetkili id: ``{interaction.user.id}``",
            color=discord.Colour.red()
        )
        banEmbed.set_image(url="https://cdn.discordapp.com/avatars/1258078864907829282/190ddf934809a6e7ca016b6f83d078a5.webp?size=1024&format=webp&width=563&height=563")
        await member.ban(reason=f"{sebep}")
        await interaction.response.send_message(f"{member}({member.id}) üyesi {interaction.user}({interaction.user.id}) tarafından sunucudan banlandı!")
        await log_channel.send(embed=banEmbed)
    else:
        await interaction.response.send_message(f"{member}({member.id}) bu komutu kullanmaya yetkin yetmiyor!")


sniped_message = None
sniped_author = None  # sniped_author değişkenini tanımlayın


@bot.event
async def on_message_delete(message):
    global sniped_message
    global sniped_author
    sniped_message = f"Message: {message.content}"
    sniped_author = f"Author: <@{message.author.id}>"


@bot.tree.command(name="snipe", description="Gets a deleted message")
async def snipe(ctx: discord.Interaction):
    global sniped_message
    global sniped_author
    if sniped_message is None:
        await ctx.response.send_message("There's nothing to snipe!")
    else:
        await ctx.response.send_message(f"{sniped_message}\n{sniped_author}")


old = None
new = None
author = None


@bot.event
async def on_message_edit(before, after):
    global old
    global new
    global author
    old = before.content
    new = after.content
    author = after.author.id


@bot.tree.command(name="edit", description="Returns an edited message")
async def edit(ctx: discord.Interaction):
    global old
    global new
    global author
    if new is None:
        await ctx.response.send_message("There's no edited message to return.")
    else:
        await ctx.response.send_message(f"Before: {old}\nAfter: {new}\nAuthor: <@{author}>")


@bot.event
async def on_member_join(member):
    hg_channel = bot.get_channel(hg_kanal_id)
    role = member.guild.get_role(kayitsiz_rol)
    await member.add_roles(role)
    await hg_channel.send(f"{member.mention}({member.id}) Sunucumuza Hoş geldin.\n üyeye <@&{kayitsiz_rol}> rolünü verdim Tıklayıp Kayıt olduktan sonra<#{kurallar_kanal_id}> kanalından sunucunun kurallarını okumayı unutma!")


@bot.event
async def on_message(message):
    log_ch = bot.get_channel(msg_log)
    if message.author.id == bot.user.id:
        return
    elif message.author.id != bot.user.id:
        await log_ch.send(f"Mesaj İçeriği: {message.content}\nMesajı gönderin kişi: {message.author}({message.author.id})")


@bot.event
async def on_message_content(message):  # on_message yerine on_message_content kullanın
    if message.content == "sa":
        embed = discord.Embed(
            title="So Cruel",
            description=f"Aleyküm Selam Dostum {message.author.mention}",
            colour=discord.Colour.purple()
        )
        embed.set_footer(text="So Cruel")
        await message.channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    bb_channel = bot.get_channel(hg_kanal_id)
    await bb_channel.send(f"{member}({member.id}) üyesi aramızdan ayrıldı bu durum bizi çok üzdü umarım geri gelirsin")


@bot.event
async def on_ready():
    print(f"{bot.user.name}, Göreve hazır")
    await bot.change_presence(activity=discord.Game(name="So Cruel <3"))
    try:
        synced = await bot.tree.sync()
        print(f" Entegre edilen slash komut sayısı: {len(synced)}")
    except Exception as a:
        print(a)


@bot.tree.command(name="timeout", description="Mutes/timeouts a member")
@commands.has_permissions(moderate_members=True)
async def timeout(ctx: discord.Interaction, member: discord.Member, reason: str = None, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0):
    if member.id == ctx.user.id:
        await ctx.response.send_message("You can't timeout yourself!")
        return
    if member.guild_permissions.moderate_members:
        await ctx.response.send_message("You can't timeout another moderator!")
        return

    duration = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    if reason is None:
        await member.timeout(duration)
        await ctx.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{ctx.user.id}>.")
    else:
        await member.timeout(duration, reason=reason)
        await ctx.response.send_message(f"<@{member.id}> has been timed out for {days} days, {hours} hours, {minutes} minutes, and {seconds} seconds by <@{ctx.user.id}> for '{reason}'.")


@timeout.error
async def timeout_error(ctx: discord.Interaction, error):
    if isinstance(error, MissingPermissions):
        await ctx.response.send_message("You don't have the 'Moderate Members' permission!")
    else:
        raise error


@bot.tree.command(name="unmute", description="Unmutes/un-timeouts a member")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx: discord.Interaction, member: discord.Member, reason: str = None):
    if reason is None:
        await member.timeout(None)  # Timeout'u kaldırmak için None geçirin
        await ctx.response.send_message(f"<@{member.id}> has been un-timed out by <@{ctx.user.id}>")
    else:
        await member.timeout(None, reason=reason)  # Timeout'u kaldırmak için None geçirin
        await ctx.response.send_message(f"<@{member.id}> has been un-timed out by <@{ctx.user.id}> for {reason}.")


@unmute.error
async def unmute_error(ctx: discord.Interaction, error):
    if isinstance(error, MissingPermissions):
        await ctx.response.send_message("You don't have the 'Moderate Members' permission!")
    else:
        raise error

@bot.tree.command(name="notify", description="Sends a DM when it is the new year")
async def notify(ctx: discord.Interaction):
    member = ctx.user.id  # interaction.user.id kullanın
    server = ctx.guild.id
    line_number = None
    try:
        with open("newyear.txt", "r") as file:
            for number, line in enumerate(file):
                if str(member) in line:
                    line_number = number
                    break
    except FileNotFoundError:
        pass  # Dosya yoksa sorun değil, yeni dosya oluşturulacak

    if line_number is None:
        try:
            with open("newyear.txt", "a") as file:
                file.write(f"{member} {server}\n")  # Her satıra yeni bir girdi ekleyin
            await ctx.user.send(f"Hello <@{ctx.user.id}>!")
            await ctx.response.send_message(f"Hi <@{member}>, I have sent you a DM!")
        except discord.errors.Forbidden:
            await ctx.response.send_message(f"Uh <@{member}>, your DMs were closed.")
        except Exception as e:
            await ctx.response.send_message(f"An error occurred: {e}")
    else:
        await ctx.response.send_message("You are already registered!")


@bot.tree.command(name="pingping", description="Wishes everyone a happy new year in 2025!")
async def pingping(ctx: discord.Interaction):
    print("pingping komutu başlatıldı")  # Hata ayıklama mesajı
    await ctx.response.defer()  # Komutun işlendiğini belirt
    print("Etkileşim ertelendi")  # Hata ayıklama mesajı

    dt = datetime.now()
    next_year = datetime(dt.year + 1, 1, 1)
    seconds_until_newyear = (next_year - dt).total_seconds()

    print(f"Yeni yıla kadar {seconds_until_newyear} saniye var")  # Hata ayıklama mesajı
    # await asyncio.sleep(seconds_until_newyear) # Bekleme süresi kaldırıldı

    try:
        with open('newyear.txt', 'r') as file:
            lines = file.readlines()  # Tüm satırları okuyun
        print("Dosya okundu")  # Hata ayıklama mesajı

        async def send_new_year_wishes():  # Asenkron fonksiyon tanımlayın
            print("Asenkron görev başlatıldı")  # Hata ayıklama mesajı
            for line in lines:
                try:
                    id, guild_id = map(int, line.strip().split())  # Satırı bölerek ID'leri alın
                    guild = bot.get_guild(guild_id)  # Guild nesnesini alın

                    if guild:
                        member = await guild.fetch_member(id)  # Üyeyi guild üzerinden alın
                        if member:
                            try:
                                await member.send(f"Happy New year <@{member.id}>! I wish you a happy 2025!")
                                await member.send("https://www.funimada.com/assets/images/cards/big/ny-666.gif")
                            except discord.errors.Forbidden:
                                # Kullanıcının DM'leri kapalıysa, genel kanala mesaj gönder
                                general_channel = find(lambda x: x.name == 'general', guild.text_channels)
                                if general_channel:
                                    await general_channel.send(f"Happy New Year <@{member.id}>! I wish you a happy 2025!")
                                else:
                                    print(f"Genel kanal bulunamadı: {guild.name}")
                            except Exception as e:
                                print(f"DM gönderilirken hata oluştu: {e}")
                        else:
                            print(f"Üye bulunamadı: {id} - {guild.name}")
                    else:
                        print(f"Guild bulunamadı: {guild_id}")
                except ValueError:
                    print(f"Geçersiz satır: {line}")
                except Exception as e:
                    print(f"Satır işlenirken hata oluştu: {e}")
            print("Asenkron görev tamamlandı")  # Hata ayıklama mesajı

        asyncio.create_task(send_new_year_wishes())  # Arka planda çalıştırın
        await ctx.followup.send("New Year wishes are being sent in the background!")
        print("Yanıt gönderildi")  # Hata ayıklama mesajı

    except FileNotFoundError:
        await ctx.followup.send("No users registered for New Year wishes.")
    except Exception as e:
        print(f"pingping komutunda hata oluştu: {e}") # Hata ayıklama mesajı
        await ctx.followup.send(f"An error occurred: {e}")


@bot.tree.command(name="time-until-2025", description="Calculates the time until 2025!")
async def until(ctx: discord.Interaction):
    await ctx.response.defer()  # Komutun işlendiğini belirt
    dt = datetime.now()
    next_year = datetime(dt.year + 1, 1, 1)
    time_difference = next_year - dt
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    await ctx.followup.send(f"{time_difference.days} days, {hours} hours, {minutes} minutes, and {seconds} seconds until 2025!")


@bot.tree.command(name="gifs", description="Sends a variety of new year gifs")
async def gifs(ctx: discord.Interaction):
    await ctx.response.send_message("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQUbLN8awQlLz3_uccao_E7kVO-9YbEH77PYA&s")

bot.run(token)