from flask import Flask, request, jsonify
import os
import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton, ForceReply, ReplyKeyboardRemove, \
    InlineKeyboardButton, InlineKeyboardMarkup
import string
import random
from dotenv import load_dotenv
import pymongo
import dns
import re
import traceback

load_dotenv()

bot = telepot.Bot(os.getenv("BOT_TOKEN"))
print(bot.getMe())
BO_TAU = os.getenv('BO_CUA_TAU')
DB_PW = os.getenv('MONGO_PW')
DB_US = os.getenv('MONGO_US')
DB_SV = os.getenv('MONGO_SV')
DB_URI = os.getenv('MONGO_URI')
print(BO_TAU)
# BOT_END_URL = os.getenv('BOT_END_URL')
# bot.setWebhook(BOT_END_URL + "/dmLocalhost")

client = pymongo.MongoClient(DB_URI)
airdropDB = client.airdropCampaign1
user_collection = airdropDB['tele_users']

id_chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
ref_id_size = 10

botResponding = {
    'start': '''Hello %s! I'm going to walk you through the steps to get your $MONES token.

Mones is a Strategy Role-Playing Game where you collect over 200 hero characters, turn them into skilled warriors through training then fight in PvE/PvP battles to take over the kingdom. Gear up to embark on a never-seen-before journey where you explore the mysterious ancient Mones land, recruit over 200 heroes, and battle epic guild wars to become the world master.

🏆 Total reward: 
💰 Winners: 3,000 random winners 
💰 Total to earn per Winner: 30 $MONES

🔹 Top 1-5 ref: 1,000 $MONES/each
🔹 Top 6-20 ref: 200 $MONES/each
🔹 Top 21-50 ref: 50 $MONES/each 

🌐 Website: https://mones.io/
⏰ Airdrop end date: February 15th
⏰ Distribution date: 7 Days After IDO (Public Sale)

✅ Complete the following steps to be eligible for the airdrop
    🔸 Join our Telegram Channel and Community Group
    🔸 Join our community on Discord Server
    🔸 Follow us on Twitter
    🔸 Like and quote tweet this Airdrop Tweet
    🔸 Like Mones Facebook Fanpage and tag 3 friends in comment
    🔸 Follow Medium

Note: 
    ✔️ All steps are mandatory and will be automatically verified.
    ✔️ Each wallet address can only be received once in the program.
    ✔️ Only use one Twitter account, one Telegram account, one Discord account and one Facebook account. If we detect you use more than one, your results will be forfeited.

When you ready to start, please click to "✍️ Submit Details"''',
    'failed_telegram': '⛔️ %s, you must join our telegram channel and group to continue! Please try again.',
    'failed_discord': "⛔️ %s, you filled invalid username#id. Please check again and submit both 'username' and 'id', with # in the middle",
    'failed_twitter_id': '⛔️ %s, you filled invalid Twitter ID, please check then submit again!',
    'failed_twitter': "⛔️ %s, you filled invalid URL. Please check then submit again! The URL should be https://twitter.com/yourusername/status/xxxxxxxxxxxxxxx",
    'failed_wallet': "⛔️ %s, Your wallet should follow as example: 0xa6f79b60359f141df90a0c745125b131caaffd12",
    'failed_facebook': '⛔️ %s, you filled invalid URL. Please check then submit again!',
    'task_telegram': '🔹 Join our [Telegram Group] (https://t.me/mones_chat)\n🔹 Join our [Telegram Channel] (https://t.me/mones_ann)\n\nAfter joined, press "✅ Check"',
    'task_discord': '🔹 Join our community on [Discord] (https://discord.gg/monesnfts)\n\nThen reply your Discord username#id  (Example: monesuser#1573)',
    'task_twitter_id': '🔹 Follow us on [Twitter] (https://twitter.com/monesnfts)\n\nOnce done, submit your Twitter username',
    'task_twitter_url': '🔹 Like, quote tweet this Airdrop Tweet on Twitter and tag 3 friends with tag #Mones #RPG #Airdrop\n\nOnce done, submit URL of your quote tweet (Example: https://twitter.com/<username>/status/1477505756920365056)',
    'task_facebook_id': '🔹 Like our Facebook Fanpage (https://www.facebook.com/monesgames)\n\nOnce done, submit the Facebook Profile URL. (Example: https://www.facebook.com/username or https://www.facebook.com/profile.php?id=xxxxxxxxx)',
    'task_facebook_url': '🔹  On Facebook, like this Airdrop Post, and tag 3 friends in comment section.\n\nWe will use automation tool to check and verify your profile in comment. Once done, click ✅ Done',
    'task_medium': "🔹 Follow Mones's Medium (https://monesnfts.medium.com)\n\nOnce done, click ✅ Done",
    'task_wallet': "✍️ Submit your AVAX C-Chain address. \n\nPlease do not submit XXXXXX address generated on exchanges (Don't use Binance, FTX Exchange, Mexc, Huobi, GATE, Kucoin or Bybit, etc...)",
    'finish': '''🌟🌟 Congratulations, %s  🌟🌟\n\n🔗 This is your referral link: %s.\n\n🤗 You should use this link to invite your friends to earn more tokens by referring them to join Monesians!\n\n🏆 We will announce the results for this airdrop on our official social channels. Stay tuned!\n\nYou can check your progression by clicking on 🥇 My Invite Stats\n\nYou can check leaderboard by clicking on 📊 Leaderboard\n------\n\nNote: You will get 1 Referral Point for each invited friend who has completed this airdrop tasks.''',
    'invite_stat': '''🔗 This is your referral link: %s\n\nNumber of people you referred: %s\n\n🤗 You should use this link to invite your friends to earn more tokens by referring them to join Monesians!''',
    'info_request': 'My Wallet: %s\n\nTwitterID: %s\n\nTwitter Quote Tweet URL: %s\n\nDiscord ID: %s\n\nFacebook Profile:%s\n\n⚠️ If something went wrong, please click Start Over to re-submit your information.',
    'useful_link': 'Please be aware of fake links. \nThese are our official links:\n\n🌐 Website: https://mones.io\n🎧 Discord: https://discord.gg/monesnfts\n👨‍✈️ Telegram Group: https://t.me/mones_chat\n👨‍✈️ Telegram Channel: https://t.me/mones_ann\n💬 Twitter: https://twitter.com/MonesNFTs\n📘 Facebook: https://www.facebook.com/monesgames/\n📝 Medium: https://monesnfts.medium.com/',
}

t_me_md = 't.me/monesAirdrop\_bot?start=%s'
t_me_nm = 't.me/monesAirdrop_bot?start=%s'

ranking_emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

keyboardLayout = {
    'start': [["✍️ Submit Details"]],
    'joinCheck': [["✅ Check"]],
    'doneFb': [["✅ Done Facebook"]],
    'doneMedium': [["✅ Done Medium"]],
    'finish': [['🥇 My Invite Stats', '🧾 My Info', '📊 Leaderboard'], ['🔗 Useful Links', '📱 Start Over']],
    'help': [['🥇 My Invite Stats', '🧾 My Info', '📊 Leaderboard'], ['🔗 Useful Links', '📱 Start Over']]
}

app = Flask('app')


@app.route('/')
def hello_world():
    return 'Hello, World!'


def id_generator():
    return ''.join(random.choice(id_chars) for _ in range(ref_id_size))


def update_db(user_info):
    user_collection.update_one({'_id': user_info["_id"]}, {"$set": user_info}, upsert=False)


def checkJoinedGroup(user_id_tele):
    try:
        userObj = bot.getChatMember(os.getenv("TELE_GROUP"), user_id_tele)
    except:
        return False
    if ('user' not in userObj.keys()):
        return False
    else:
        if (userObj['status'] == 'left'):
            return False
        else:
            return (not userObj['user']['is_bot'])


def checkJoinedChannel(user_id_tele):
    try:
        userObj = bot.getChatMember(os.getenv("TELE_CHANNEL"), user_id_tele)
    except:
        return False
    if ('user' not in userObj.keys()):
        return False
    else:
        if (userObj['status'] == 'left'):
            return False
        else:
            return (not userObj['user']['is_bot'])


def validTwitteUser(sn):
    matched = re.match(r'^[a-zA-Z0-9_]{1,15}$', sn)
    if (matched == None):
        return False
    else:
        return True


@app.route('/dmLocalhost', methods=["POST", "GET"])
def recv_from_telegram():
    t_data = request.get_json(silent=True)
    print(t_data)
    try:
        t_message = t_data["message"]
    except Exception as e:
        bot.sendMessage(BO_TAU, str(e))
        bot.sendMessage(BO_TAU, str(t_data))
        return 'error vler'

    try:
        t_chat = t_message["chat"]
    except Exception as e:
        bot.sendMessage(BO_TAU, str(e))
        bot.sendMessage(BO_TAU, str(t_message))
        return jsonify({"ok": "POST request processed"})

    try:
        user_input = t_message["text"].strip()
    except:
        return 'Bypass caused Joined Group or Channel'

    # text = text.lstrip("/")
    user_local = user_collection.find_one({"chat_id": t_chat["id"]})
    if not user_local:
        id_generated = id_generator()
        user_local = {
            "chat_id": t_chat["id"],
            'refs': 0,
            'ref_id': id_generated,
            'discord_id': '',
            'twitter_id': '',
            'twitter_url': '',
            'fb_url': '',
            'medium': False,
            'wallet': '',
            'refferer': '',
            'lastStep': 0,
            'plus_ref': False
        }
        response = user_collection.insert_one(user_local)
        # we want chat obj to be the same as fetched from collection
        user_local["_id"] = response.inserted_id
    msgSender = t_chat["id"]
    try:
        if ('/start' in user_input or user_input == '📱 Start Over'):
            if (' ' in user_input):
                if (user_local['refferer'] == ''):
                    ref_from = user_input.split(' ')[1]
                    if (len(ref_from) == 10):
                        user_local['refferer'] = ref_from
                else:
                    user_local['refferer'] = 'nope'
            user_local['lastStep'] = 1
            update_db(user_local)
            bot.sendMessage(msgSender, botResponding['start'] % (t_chat['first_name']), parse_mode="Markdown",
                            reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['start'], one_time_keyboard=True,
                                                             resize_keyboard=True))
        elif (user_input == '/myinfo' or user_input == '🧾 My Info'):
            responding = botResponding['info_request'] % (
                user_local['wallet'], user_local['twitter_id'], user_local['twitter_url'], user_local['discord_id'],
                user_local['fb_url'])
            bot.sendMessage(msgSender, responding, parse_mode="Markdown", disable_web_page_preview=True)
        elif (user_input == '/help'):
            responding = "What can I help you?"
            bot.sendMessage(msgSender, responding, reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['help']))
        elif (user_input == '🔗 Useful Links'):
            bot.sendMessage(msgSender, botResponding['useful_link'], disable_web_page_preview=True)
        elif (user_input == '📊 Leaderboard'):
            # responding = botResponding['invite_stat'] % (t_me_nm % (user_local['ref_id']))
            top10User = user_collection.find().sort('refs', -1).limit(10)
            responding = 'Highest Referrals - Top %s Highest Point:\n\n'
            i = 0
            for user_ in top10User:
                responding += ranking_emoji[i] + ' Refers: ' + str(user_['refs']).rjust(5, " ") + ' - ' + user_[
                                                                                                              'wallet'][
                                                                                                          :20] + '.....\n'
                i += 1
            bot.sendMessage(msgSender, responding % str(i), disable_web_page_preview=True)
        elif (user_input == '🥇 My Invite Stats'):
            responding = botResponding['invite_stat'] % (t_me_nm % (user_local['ref_id']), str(user_local['refs']))
            bot.sendMessage(msgSender, responding, disable_web_page_preview=True)
        else:
            if (user_input == "✍️ Submit Details" or user_local['lastStep'] <= 1):
                user_local['lastStep'] = 2
                update_db(user_local)
                bot.sendMessage(msgSender, botResponding['task_telegram'], disable_web_page_preview=True,
                                reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['joinCheck'],
                                                                 one_time_keyboard=True, resize_keyboard=True))
            elif (user_local['lastStep'] <= 2):
                if (checkJoinedChannel(msgSender) and checkJoinedGroup(msgSender)):
                    user_local['lastStep'] = 3
                    update_db(user_local)
                    bot.sendMessage(msgSender, botResponding['task_discord'], disable_web_page_preview=True)
                else:
                    bot.sendMessage(msgSender, botResponding['failed_telegram'] % (t_chat['first_name']),
                                    disable_web_page_preview=True,
                                    reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['joinCheck'],
                                                                     one_time_keyboard=True, resize_keyboard=True))
            elif (user_local['lastStep'] <= 4):
                if ('#' in user_input):
                    user_local['lastStep'] = 5
                    user_local['discord_id'] = user_input.strip()
                    update_db(user_local)
                    bot.sendMessage(msgSender, botResponding['task_twitter_id'], disable_web_page_preview=True)
                else:
                    bot.sendMessage(msgSender, botResponding['failed_discord'] % (t_chat['first_name']))

            elif (user_local['lastStep'] <= 6):
                if (validTwitteUser(user_input)):
                    user_local['lastStep'] = 7
                    user_local['twitter_id'] = user_input.strip()
                    update_db(user_local)
                    bot.sendMessage(msgSender, botResponding['task_twitter_url'], disable_web_page_preview=True)
                else:
                    bot.sendMessage(msgSender, botResponding['failed_twitter_id'] % (t_chat['first_name']))
            elif (user_local['lastStep'] <= 8):
                if ('twitter.com/' + user_local['twitter_id'].lower() in user_input.lower()):
                    user_local['lastStep'] = 9
                    user_local['twitter_url'] = user_input.strip()
                    update_db(user_local)
                    bot.sendMessage(msgSender, botResponding['task_facebook_id'])
                else:
                    bot.sendMessage(msgSender, botResponding['failed_twitter'] % (t_chat['first_name']),
                                    parse_mode="Markdown", disable_web_page_preview=True)
            elif (user_local['lastStep'] <= 10):
                if ('facebook.com/' in user_input.lower()):
                    user_local['lastStep'] = 11
                    user_local['fb_url'] = user_input
                    update_db(user_local)
                    bot.sendMessage(msgSender, botResponding['task_facebook_url'], parse_mode="Markdown",
                                    disable_web_page_preview=True,
                                    reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['doneFb'],
                                                                     one_time_keyboard=True, resize_keyboard=True))
                else:
                    bot.sendMessage(msgSender, botResponding['failed_facebook'] % (t_chat['first_name']))
            elif (user_local['lastStep'] <= 12 and 'Done Facebook' in user_input):
                user_local['lastStep'] = 13
                update_db(user_local)
                bot.sendMessage(msgSender, botResponding['task_medium'], parse_mode="Markdown",
                                disable_web_page_preview=True,
                                reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['doneMedium'],
                                                                 one_time_keyboard=True, resize_keyboard=True))
            elif (user_local['lastStep'] <= 14 and 'Done Medium' in user_input):
                user_local['lastStep'] = 15
                update_db(user_local)
                bot.sendMessage(msgSender, botResponding['task_wallet'], parse_mode="Markdown",
                                disable_web_page_preview=True)
            elif (user_local['lastStep'] <= 16):
                print(user_input)
                if ('0x' in user_input and len(user_input) == 42):
                    user_local['wallet'] = user_input
                    user_local['lastStep'] = 17

                    if (user_local['refferer'] != '' and user_local['refferer'] != 'nope' and not user_local[
                        'plus_ref']):
                        ref_id_from = user_local['refferer']
                        ref_user_local = user_collection.find_one({"ref_id": ref_id_from})
                        ref_user_local['refs'] += 1
                        user_local['plus_ref'] = True
                        update_db(ref_user_local)
                    update_db(user_local)
                    responding = botResponding['finish'] % (t_chat['first_name'], t_me_nm % (user_local['ref_id']))
                    bot.sendMessage(msgSender, responding, disable_web_page_preview=True,
                                    reply_markup=ReplyKeyboardMarkup(keyboard=keyboardLayout['finish'],
                                                                     resize_keyboard=True))
                else:
                    bot.sendMessage(msgSender, botResponding['failed_wallet'] % (t_chat['first_name']))

    except Exception as e:
        print("ERROR : " + str(e))
        bot.sendMessage(BO_TAU, "Error VL ong gia oi!")
        bot.sendMessage(BO_TAU, str(e))
        bot.sendMessage(BO_TAU, str(traceback.format_exc()))

    return jsonify({"ok": "POST request processed"})


try:
    app.run(host='0.0.0.0', port=8081)
except:
    client.close()
