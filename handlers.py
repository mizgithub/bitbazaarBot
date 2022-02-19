from telegram import(
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove, Update,
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
)
from telegram.ext import(
    CommandHandler, CallbackContext,
    ConversationHandler, MessageHandler,
    Filters, Updater, CallbackQueryHandler
)
from config import(
    api_key,
    api_secret,
    FAUNA_KEY
)

import cloudinary
from cloudinary.uploader import upload
# from faunadb import query as q
# from faunadb.client import FaunaClient
# from faunadb.errors import NotFound
import psycopg2
import qrcode
# from PIL import Image
# from io import BytesIo
# configure cloudinary
cloudinary.config(
    cloud_name = "mizanu",
    api_key = api_key,
    api_secret = api_secret,
)

conn = psycopg2.connect(
    host="ec2-18-235-114-62.compute-1.amazonaws.com",
    database="dquhcsdnk10o",
    user="rqbdhhwmqbdxvg",
    port = "5432"
    password="32f33e6febfa64aac2262d67ca47d5b59575de4dac475ed553e49c6c0430a18d")
cur = conn.cursor()
#fauna client configure
#client = FaunaClient(secret = FAUNA_KEY)

cur.execute("Create table customer(phone varchar(13), secrete varchar(10))")
cur.execute("Create table category(id serial primary key, name varchar(50))")
cur.execute("Create table product (id serial primary key, cid integer, name varchar(100), prod_desc varchar(500), price integer, amount integer, max_amount integer, image_href varchar(500))")
cur.execute("Create table cart(id serial primary key, custId integer, pId integer, amount integer, total_price integer)")
cur.execute("Create table admin(username varchar(50), password varchar(50))")
cur.execute("Create table agent(username varchar(50), password varchar(50))")
cur.execute("insert into admin values('miz', 'miz123')")


# define options



GET_SECRET, CUSTOMER_HOME, REGISTRATION_PAGE, AUTHENTICATE_ADMIN,ADMIN_ACTIONS,MANAGE_CATEGORY,ADD_CATEGORY, ADD_AGAIN, MANAGE_PRODUCT, ADD_PRODUCT,EDIT_PRODUCT,DELETE_PRODUCT,SHOW_PRODUCT_DETAIL, CUST_CATEGORIES, CUST_PRODUCTS,CUST_FAVORITES,CUST_DEALS,ADD_TO_CART,SHOW_PRODUCTS_FROM_CAT,REGISTER_ORDER,GENERATE_QRCODE = range(21)

selected_cat = 0
selected_cust = 0
logedin_admin = 0
selected_prod = 0

# adding handler methods
#--------------- START CUSTOMER OPERATIONS -------------------------------------------------------------
def start(update, context:CallbackContext)->int:
    bot = context.bot
    chat_id = update.message.chat.id
    help_message = "Welcome to Bitbazaar\n/login\n/Register - > If you are new\n/Help\n/About - > About Bitbazaar\n/Contact_us\n/Logout"
    bot.send_message(chat_id = chat_id, text="Well come to bitbazaar\n Loging Enter your phone\n"+help_message)
def login(update, context:CallbackContext)->int:
    bot = context.bot
    chat_id = update.message.chat.id
    user = update.message.from_user
    bot.send_message(chat_id = chat_id, text="Please enter your secret code (Minimium 4 digit)")
    return GET_SECRET
def contact(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(chat_id = chat_id, text = "Bitbazaar customer support\nEmail: bitbazaar_ethiopia@gmail.com\nTelephone: +251909879898")
def register(update, context:CallbackContext)->int:
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(chat_id = chat_id, text = "Enter a simple secret code (minimum 4 digit maximum 10 digit)")
    return REGISTRATION_PAGE
def handle_registration(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    user_message = update.message.text
    user_id = update.message.from_user['id']
    cur.execute("insert into customer values("+str(user_id)+", '"+str(user_message)+"')")
    bot.send_message(chat_id  = chat_id, text="Registration completed\n/Login to login to the bot")
def cancel(update, context):
    update.message.reply_text(
        'Bye! I hope we can talk again some day.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END
def accept_secret_code(update, context:CallbackContext)->int:
    bot = context.bot
    chat_id = update.message.chat.id
    user_message = update.message.text
    phone = update.message.from_user['id']
    if len(user_message)<4:
        print("Less than 4")
        bot.send_message(chat_id = chat_id,text="Please enter a secret code with 4 Minimium Digits\nStart over /Login")
        return ConversationHandler.END
    else:
        cur.execute("select * from customer where phone = '"+str(phone)+"' and secrete = '"+str(user_message)+"'")
        data = cur.fetchall()

        ##Creating inline buttons
        if len(data)>0:
            cust_menu = [
                    [
                        KeyboardButton(
                            "📂 Categories"
                        ),
                        KeyboardButton(
                            "🧳 Products"
                        ),
                        KeyboardButton(
                            "🤝 My deals"
                        )
                    ],
                    [
                        KeyboardButton(
                            "❤️ Favorites"
                        ),
                        KeyboardButton(
                            "🗝 Change password"
                        ),
                        KeyboardButton(
                            "🙌 Logout"
                        )
                ],
            ]
            global selected_cust
            selected_cust = phone
            bot.send_message(chat_id = chat_id, text="Welcome to BitBazaar Once Again", reply_markup = ReplyKeyboardMarkup(cust_menu))
            return CUSTOMER_HOME
        else:
            bot.send_message(chat_id = chat_id, text="Incorrect secret code. Try again /Login\nIf you are new Please register here /Register")
            return ConversationHandler.END
def customer_home(update, context:CallbackContext)->int:
    bot = context.bot
    chat_id = update.message.chat.id
    user_message = update.message.text

    if user_message == "📂 Categories":
        #show customer categories
        data = getCategories()
        cat_list = []
        for d in data:
            cat_list.append( [InlineKeyboardButton(text = str(d[1])+" ("+str(num_products(d[0]))+")", callback_data = d[0])] )
        bot.send_message(chat_id = chat_id,text = "📂 Categories", reply_markup = InlineKeyboardMarkup(cat_list))
        return SHOW_PRODUCTS_FROM_CAT
    elif user_message == "🧳 Products":
        prod = consumer_get_product("all")
        if len(prod)<=0:
            bot.send_message(chat_id = chat_id, text="No product found")
            return CUSTOMER_HOME
        else:
            pro_list = []
            for p in prod:
                p_id = p[0]
                name = p[2]
                description = p[3]
                amount = p[5]
                price = p[4]
                max_order = p[6]
                photo = p[7]
                addTo_cart_button = [
                    [
                        InlineKeyboardButton(text="🛒 Add to cart", callback_data=p_id)
                    ]
                ]
                bot.send_photo(
                    chat_id = chat_id,
                    caption = str(name)+"\n"+"📃 "+str(description)+" \n --- \n⚠️Product left: "+str(amount)+"\n💰 "+str(price)+" ETB \n---\n♾Max amount one can order: "+str(max_order),
                    photo=photo,
                    reply_markup = InlineKeyboardMarkup(addTo_cart_button)
                    )
            return ADD_TO_CART
    elif user_message == "🤝 My deals":
        deals_data = get_customer_deals()
        if len(deals_data)<=0:
            bot.send_message(chat_id = chat_id, text="You have no item in cart.\nWhen you add a product to cart it will apear here ")
        else:
            for d in deals_data:
                d_pro = d[2]
                d_amount = d[3]
                d_id = d[0]
                d_price = d[4]
                cur.execute("select name,amount from product where id="+str(d_pro))
                pro_data = cur.fetchall()
                pro_name = pro_data[0][0]
                pro_amount_left = pro_data[0][1]
                ticket_button = [[]]
                if int(pro_amount_left)>0:
                    ticket_button[0].append(InlineKeyboardButton(text="On progress", callback_data="on"))
                else:
                    ticket_button[0].append(InlineKeyboardButton(text="Get ticket", callback_data=str(d_id)))
                bot.send_message(chat_id = chat_id, text="🎁"+str(pro_name)+"\n 🛒Amount you ordered: "+str(d_amount)+"\n💰 Total price:"+str(d_price)+"ETB", reply_markup = InlineKeyboardMarkup(ticket_button))
                return GENERATE_QRCODE
    return CUSTOMER_HOME
def generate_qr_code(update, context:CallbackContext)->int:
    #generating qr code
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    if str(user_message) == "on":
        bot.send_message(chat_id = chat_id, text="The deal is on progress.")
    else:
        img = qrcode.make(str(user_message))
        img.save("qrCode.jpeg")
        bot.send_photo(chat_id = chat_id, photo = open("qrCode.jpeg",'rb'), caption="Save it to your gallary and Take it with you when collecting your orders")
    return CUSTOMER_HOME
def get_customer_deals():
    cur.execute("select * from cart where custId='"+str(selected_cust)+"'")
    data = cur.fetchall()
    return data
def show_products_from_category(update, context:CallbackContext)->int:
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    prod = consumer_get_product(user_message)
    if len(prod)<=0:
        bot.send_message(chat_id = chat_id, text="No product found from the selected category")
        return CUSTOMER_HOME
    else:
        pro_list = []
        for p in prod:
            p_id = p[0]
            name = p[2]
            description = p[3]
            amount = p[5]
            price = p[4]
            max_order = p[6]
            photo = p[7]
            addTo_cart_button = [
                [
                    InlineKeyboardButton(text="🛒 Add to cart", callback_data=p_id)
                ]
            ]
            bot.send_photo(
                chat_id = chat_id,
                caption = str(name)+"\n"+"📃 "+str(description)+" \n --- \n⚠️Product left: "+str(amount)+"\n💰 "+str(price)+" ETB \n---\n♾Max amount one can order: "+str(max_order),
                photo=photo,
                reply_markup = InlineKeyboardMarkup(addTo_cart_button)
                )
        return ADD_TO_CART
def consumer_get_product(cat):
    if cat=="all":
        cur.execute("select * from product where amount > 0")
        data = cur.fetchall()
        return data
    else:
        cur.execute("select * from product where cid = "+str(cat)+" and amount > 0")
        data = cur.fetchall()
        return data
def add_to_cart(update, context:CallbackContext)->int:
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    global selected_prod
    selected_prod = user_message
    bot.send_message(chat_id = chat_id, text="Enter amount\nCheck max amount one can order")
    return REGISTER_ORDER
def register_order(update:Update, context:CallbackContext)->int:
    # chat_id = update.message.chat.id
    bot = context.bot
    user_message = update.message.text
    print(user_message)
    if user_message.isdigit():
        if int(user_message)<=0:
            update.message.reply_text("Please enter valid amount")
            # bot.send_message(chat_id = chat_id, text="Please enter valid amount")
            return REGISTER_ORDER
        else:
            response = update_customer_cart(user_message)
            if response == "success":
                update.message.reply_text("Product added to art")
                # bot.send_message(chat_id = chat_id, text="Product has been successfully added to your cart\nClick on <<My Cart to see your orders>>")
                return CUSTOMER_HOME
            else:
                update.message.reply_text(str(response))
                # bot.send_message(chat_id = chat_id, text=response)
                return REGISTER_ORDER
    else:
        bot.send_message(chat_id = chat_id, text="Please enter valid amount")
        return REGISTER_ORDER
def update_customer_cart(amount):
    #first get product info  customer cart
    cur.execute("select * from product where id="+str(selected_prod))
    pro_data = cur.fetchall()
    pro_data = pro_data[0]
    # p_id = p[0]
    # name = p[2]
    # description = p[3]
    # amount = p[5]
    # price = p[4]
    # max_order = p[6]
    # photo = p[7]
    pro_left = pro_data[5]
    pro_price = pro_data[4]
    pro_id = pro_data[0]
    pro_max_order = pro_data[6]
    if int(amount)>pro_max_order:
        return "Max amount you can order is"+str(pro_max_order)
    # chek customers cart
    else:
        cur.execute("select * from cart where custId='"+str(selected_cust)+"' and pId="+str(pro_id))
        cart_data = cur.fetchall()
        if len(cart_data)<=0:
            #insert to cart
            total_price = int(amount)*int(pro_price)
            cur.execute("insert into cart(custId,pId,amount,total_price) values ('"+str(selected_cust)+"', "+str(pro_id)+", "+str(amount)+", "+str(total_price)+")")
            pro_left = int(pro_left)- int(amount)
            cur.execute("update product set amount="+str(pro_left)+"  where id="+str(pro_id))
            return "success"
        else:
            #check prev order amount
            cart_data = cart_data[0]
            prev_amount = cart_data[3]
            if int(prev_amount)+int(amount)<=pro_max_order:
                #update cart
                total_amount = int(prev_amount)+int(amount)
                total_price = total_amount * int(pro_price)
                cur.execute("update cart set amount ="+str(total_amount)+", total_price ="+str(total_price)+" where custId='"+str(selected_cust)+"' and pId="+str(pro_id))
                pro_left = int(pro_left)- int(amount)
                cur.execute("update product set amount="+str(pro_left)+"  where id="+str(pro_id))
                return "success"
            else:
                return "You have "+str(prev_amount)+" of previous orders\nMax amount you can order is"+str(pro_max_order)

#----- END customer operations ---------------------------------------------------------------------------







#------------ START Admin operations -------------------------------------------------------------------------
def admin(update,context):
    bot = context.bot
    chat_id = update.message.chat.id
    bot.send_message(chat_id = chat_id, text="Enter your username and password\ncomma separated")
    return AUTHENTICATE_ADMIN
def authenticate_admin(update, context):
    bot = context.bot
    chat_id = update.message.chat.id
    user_message = update.message.text
    user_message = user_message.split(",")
    if len(user_message)<2:
        bot.send_message(chat_id = chat_id, text="Invalid Input. Start over /Admin")
        return ConversationHandler.END
    else:
        cur.execute("select * from admin where username='"+str(user_message[0])+"' and password='"+str(user_message[1])+"'")
        data = cur.fetchall()
        if len(data)>0:
            admin_menu = [
                [
                    KeyboardButton(
                        "Manage categories"
                    ),
                    KeyboardButton(
                        "Customer orders"
                    ),
                    KeyboardButton(
                        "Manage Locations"
                    )
                ],
                [
                    KeyboardButton(
                        "Change password"
                    ),
                    KeyboardButton(
                        "Create agent"
                    ),
                    KeyboardButton(
                        "Logout"
                    )
                ],
            ]
            bot.send_message(chat_id = chat_id,text="Wellcome", reply_markup = ReplyKeyboardMarkup(admin_menu))
            return ADMIN_ACTIONS
def admin_actions(update, context:CallbackContext)->int:
    chat_id = update.message.chat.id
    bot = context.bot
    button_data = update.message.text
    # bot.send_message(chat_id = chat_id, text=str(button_data))
    if button_data == "Manage categories":
        cat = getCategories()
        cat_key = [[]]
        for c in cat:
            cat_key[0].append(InlineKeyboardButton(text = c[1]+"("+str(num_products(c[0]))+")", callback_data=str(c[0])))
        cat_key[0].append(InlineKeyboardButton(text="Add category", callback_data="add"))
        bot.send_message(chat_id = chat_id, text = "Categories", reply_markup = InlineKeyboardMarkup(cat_key))
        return MANAGE_CATEGORY
    elif button_data == "Manage products":
        bot.send_message(chat_id = chat_id, text = "Manage products")
    elif button_data == "Customers":
        bot.send_message(chat_id = chat_id, text = "cstomers")
    elif button_data == "Change password":
        bot.send_message(chat_id = chat_id, text="Change password")
    elif button_data == "Create agent":
        bot.send_message(chat_id = chat_id, text="Create agent")
    elif button_data == "Logout":
        bot.send_message(chat_id = chat_id, text="Logout")
def check_if_the_user_click_admin_menus(user_message):
    if user_message == "Manage categories":
        return True;
def getCategories():
    cur.execute("select * from category")
    cat = cur.fetchall()
    return cat
def num_products(cat):
    cur.execute("select count(*) from product where cid="+str(cat))
    num_prod = cur.fetchall()
    return num_prod[0][0]
def get_products(cat):
    cur.execute("select * from product where cid="+str(cat))
    pro = cur.fetchall()
    return pro
def manage_category(update, context:CallbackContext)->int:
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    if user_message =="add":
        bot.send_message(chat_id = chat_id, text="Enter category name")
        return ADD_CATEGORY
    else:
        global selected_cat
        selected_cat = user_message
        pro = get_products(int(user_message))
        pro_list = [[]]
        for p in pro:
            pro_list[0].append(InlineKeyboardButton(text= p[2], callback_data = p[0]))
        pro_list[0].append(InlineKeyboardButton(text = "Add product", callback_data="add pro"))
        bot.send_message(chat_id = chat_id, text="Products", reply_markup = InlineKeyboardMarkup(pro_list))
        return MANAGE_PRODUCT
def add_category(update, context:CallbackContext)->int:
    chat_id = update.message.chat.id
    bot = context.bot
    user_message = update.message.text
    if len(user_message)>0:
        cur.execute("insert into category(name) values('"+user_message+"')")
        cat_key = [[InlineKeyboardButton(text="Add category", callback_data="add")]]
        bot.send_message(chat_id = chat_id, text = "successfully added", reply_markup = InlineKeyboardMarkup(cat_key))
    else:
        cat_key = [[InlineKeyboardButton(text="Add category", callback_data="add")]]
        bot.send_message(chat_id = chat_id, text = "Empty value", reply_markup = InlineKeyboardMarkup(cat_key))
    return ADD_AGAIN
def add_again(update, context:CallbackContext)->int:
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    bot.send_message(chat_id = chat_id, text="Enter category name")
    return ADD_CATEGORY
def manage_product(update, context:CallbackContext)->int:
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    if user_message == "add pro":
        bot.send_message(chat_id = chat_id, text="Upload photo with caption\nThe Caption must contain\nname,desciption,price,amount,max_order\nin order separated by comma ")
        return ADD_PRODUCT
    else:
        global selected_prod
        selected_prod = user_message
        pro_options = [
            [
                InlineKeyboardButton(text = "Show details", callback_data = "s_d")
            ],
            [
                InlineKeyboardButton(text=" \U0000274c	Delete Product", callback_data = "d"),]
            ]
        bot.send_message(chat_id = chat_id, text="Choose action", reply_markup = InlineKeyboardMarkup(pro_options))
        return EDIT_PRODUCT
def add_product(update:Update, context:CallbackContext)->int:
    data = update.message
    bot = context.bot
    photo = bot.getFile(update.message.photo[-1].file_id)
    file_ = open('product_image', 'wb')
    photo.download(out = file_)
    data = update.message.caption.split(',')
    send_photo  = upload('product_image', width = 300, height =300,crop = 'thumb')
    cur.execute("insert into product(name, cid,prod_desc, price, amount, max_amount,image_href) values('"+data[0]+"', "+str(selected_cat)+",'"+data[1]+"', "+str(data[2])+", "+str(data[3])+", "+str(data[4])+",'"+send_photo['secure_url']+"')")
    pro_key = [[
        InlineKeyboardButton(text = "Add another product", callback_data = "add pro")
    ]]
    update.message.reply_text("Product added successfully",
            reply_markup = InlineKeyboardMarkup(pro_key)
        )
    return MANAGE_PRODUCT
def edit_product(update, context):
    chat_id = update.callback_query.message.chat.id
    bot = context.bot
    user_message = update.callback_query.data
    if user_message == "s_d":
        cur.execute("select * from product where id="+str(selected_prod))
        data = cur.fetchall()
        data = data[0]
        name = data[2]
        description = data[3]
        amount = data[5]
        price = data[4]
        max_order = data[6]
        photo = data[7]

        bot.send_photo(
            chat_id = chat_id,
            caption = str(name)+"\n"+"📃 "+str(description)+" \n --- \n⚠️Product left: "+str(amount)+"\n💰 "+str(price)+" ETB \n---\n♾Max amount one can order: "+str(max_order),
            photo=photo
        )
    elif user_message == "d":
        bot.send_message(chat_id = chat_id, text="Are you sure? write Y or N")
        return DELETE_PRODUCT
def delete_product(update, context):
    chat_id = update.message.chat.id
    bot = context.bot
    user_message = update.message.text
    if user_message.lower() == 'y':
        #delete product
        cur.execute("delete from product where id="+str(selected_prod))
        bot.send_message(chat_id = chat_id, text=str(selected_prod)+"has been deleted suucessfully")
