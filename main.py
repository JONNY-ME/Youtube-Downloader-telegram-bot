
'''
installation 

	sudo curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl
	sudo chmod a+rx /usr/local/bin/youtube-dl

	pip install python-decouple
	pip install python-telegram-bot
	pip install uuid


'''

import os
import uuid
from telegram import *
from telegram import utils
from telegram.ext import *
from decouple import config
import sqlite3 as sl



Admin_id = None  # your telegram id
con = sl.connect('users.db', check_same_thread=False)
try:
    con.execute("""
            CREATE TABLE USER (
                id TEXT NOT NULL PRIMARY KEY,
                name TEXT,
                role TEXT, 
                deleted TEXT
            );
        """)
except:
    pass
sql = 'INSERT INTO USER (id, name, role, deleted) values(?, ?, ?, ?)'



def get_available_formats(link):
	path = str(uuid.uuid1())
	os.mkdir(path)
	os.system(f"youtube-dl -F {link} > {path}/temp.txt")
	data = {}
	with open(f'{path}/temp.txt', 'r') as f:
		_ = [f.readline() for i in range(3)]
		q = ['very high quality', 'high quality', 'midium quality', 'low quality']
		while 1:
			try:
				k = f.readline()
				if k == '':
					break
				t = k.split()
				a, b, c, d = t[:4]
				if c == 'audio':
					data['audio '+t[-1]] = a
				elif b == 'mp4':
					data['mp4 '+ d+' '+t[-1]] = a
			except:
				break
	os.system(f'rm -rf {path}')
	return data



def download_file(format, link):
	path = str(uuid.uuid1())
	os.mkdir(path)
	os.system(f"youtube-dl -f {format} {link} -o {path}/%\(title\)s.%\(ext\)s")
	return path



def start(update, context):
	data = (str(update.message.chat_id), update.message.from_user['first_name'], 'user', 'NO')
	try:
		cur = con.cursor()
		cur.execute(sql, data)
		con.commit()
		name = utils.helpers.mention_html(update.message.chat_id, update.message.from_user['first_name'])
		context.bot.send_message(chat_id=Admin_id, 
		 	text=f"new user:-\n{name} started the bot",
		 	parse_mode=ParseMode.HTML)
		update.message.reply_text("welcome! send me a youtube link or use @vid to search for youtube videos then I will download your video in either audio or video format😊")
	except Exception as e:
		com = 'UPDATE USER SET deleted="NO" WHERE id="'+str(update.message.chat_id)+'"'
		cur = con.cursor()
		cur.execute(com)
		update.message.reply_text("welcome! send me a youtube link or use @vid to search for youtube videos then I will download your video in either audio or video format😊")



def no_of_users(update, context):
	user_id = update.message.from_user['id']
	if user_id == Admin_id:
		com = 'SELECT COUNT(*) FROM USER WHERE deleted="NO"'
		cur = con.cursor()
		data = cur.execute(com)
		num1 = None
		for i in data:
			num1 = i[0]
		com = 'SELECT COUNT(*) FROM USER WHERE deleted="YES"'
		cur = con.cursor()
		data = cur.execute(com)
		num2 = None
		for i in data:
			num2 = i[0]
		update.message.reply_text(f"the number of users is {num1+num2}\nactive = {num1}\ndeleted = {num2}")


def help(update, context):
	user_id = update.message.from_user['id']
	if user_id == Admin_id:
		update.message.reply_text(
			"list of commands\n/start to restart the bot\n/users to get number of users\n/message send message to users"
			) 


def button(update, context):
    query = update.callback_query
    query.answer()
    query.delete_message()
    if float(query.data.split()[-1][:-3]) > 49:
    	query.message.reply_text("file size must be less than 50MB")
    else:
	    data = context.user_data['data']
	    link = context.user_data['link']
	    tmp = query.message.reply_text("downloading... ")
	    path = download_file(data[query.data], link)
	    file = 	os.listdir(path)[0]
	    dn_path = path + '/' + file
	    del context.user_data['data']
	    del context.user_data['link']
	    context.bot.edit_message_text(text="uploading... ", chat_id=tmp['chat']['id'], message_id=tmp['message_id'])
	    if 'audio' in query.data:
	    	query.message.reply_audio(open(dn_path, 'rb'), caption="by @ready2talk")
	    else:
	    	query.message.reply_video(open(dn_path, 'rb'), caption="by @ready2talk")
	    context.bot.delete_message(chat_id=tmp['chat']['id'], message_id=tmp['message_id'])
	    os.system(f'rm -rf {path}')	



def message(update, context):
	update.message.reply_text(
		"send me the text that you want to send to the users or send cancel", 
		reply_markup=ReplyKeyboardMarkup([["cancel"]], one_time_keyboard=True, resize_keyboard=True))
	context.user_data['message'] = 1



def func(update, context):
	text = update.message.text
	if 'done' in context.user_data and update.message.chat_id == Admin_id:
		if text == 'cancel':
			update.message.reply_text("canceled", reply_markup=ReplyKeyboardRemove())
			del context.user_data['done']
			del context.user_data['message']
		else:
			com = 'SELECT * FROM USER'
			cur = con.cursor()
			data = cur.execute(com)
			mess = context.user_data['message']
			for id, name, _, delt in data:
				out = f"Hello {utils.helpers.mention_html(id, name)}\n"+mess
				if delt == "NO":
					try:
						context.bot.send_message(chat_id=int(id), text=out, parse_mode=ParseMode.HTML)
					except:
						com = 'UPDATE USER SET deleted="YES" WHERE id="'+id+'"'
						cur = con.cursor()
						cur.execute(com)
			del context.user_data['message']
			del context.user_data['done']
			update.message.reply_text("succesfully sent to all users", reply_markup=ReplyKeyboardRemove())
	elif 'message' in context.user_data and update.message.chat_id == Admin_id:
		if text == 'cancel':
			update.message.reply_text("canceled", reply_markup=ReplyKeyboardRemove())
			del context.user_data['message']
		else:
			update.message.reply_text("the message will be sent to all users if you enter done else enter cancel", 
				reply_markup=ReplyKeyboardMarkup([["done", 'cancel']], one_time_keyboard=True, resize_keyboard=True)
				)
			context.user_data['message'] = text
			context.user_data['done'] = 1
	else:
		# elif 'data' not in context.user_data:		
		data = get_available_formats(text)
		if data != {}:
			context.user_data['link'] = text
			context.user_data['data'] = data
			keyboard = []
			keys = list(data.keys())
			for i in range(len(keys)//2):
				keyboard.append([
					InlineKeyboardButton(f"{keys[2*i]}", callback_data=f'{keys[2*i]}'),
					InlineKeyboardButton(f"{keys[2*i+1]}", callback_data=f'{keys[2*i+1]}')
				]) 
			reply_markup = InlineKeyboardMarkup(keyboard)
			update.message.reply_text('choose format', reply_markup=reply_markup)
		# except Exception as e:
		# 	print(e)
		# 	del context.user_data['data']
		# 	del context.user_data['link']
		# 	update.message.reply_text("invallid link!")
def get_database(update, context):
	# dispatcher.add_handler(CommandHandler('get_database', get_database))
    if update.message.chat_id == Admin_id:
        context.bot.send_document(document=open('users.db', 'rb'), chat_id=Admin_id)

def main():
	updater = Updater("YOUR-API")
	dispatcher = updater.dispatcher
	dispatcher.add_handler(CommandHandler("start", start))
	dispatcher.add_handler(CommandHandler("help", help))
	dispatcher.add_handler(CommandHandler("users", no_of_users))
	dispatcher.add_handler(CommandHandler("message", message))
	dispatcher.add_handler(CommandHandler('get_database', get_database))
	dispatcher.add_handler(MessageHandler(Filters.text, func))
	updater.dispatcher.add_handler(CallbackQueryHandler(button))
	updater.start_polling()
	updater.idle()



if __name__ == "__main__":
	main()
