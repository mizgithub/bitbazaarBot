import handlers
from telegram.ext import(
    CommandHandler, CallbackContext,ConversationHandler,MessageHandler,Filters,Updater,CallbackQueryHandler
)
from config import TOKEN
import os
PORT = int(os.environ.get('PORT', 5000))
#states
#*************** Functions customers ***********

#**************** End functions ************

updater = Updater(TOKEN)
#print(updater)
 # Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)
enty_commands = [
    CommandHandler('Start', handlers.start),
    CommandHandler('Login', handlers.login),
    CommandHandler('Contact', handlers.contact),
    CommandHandler('Register', handlers.register),
    CommandHandler('Admin', handlers.admin)
]
com_handlers = ConversationHandler(
    entry_points=enty_commands,
    states={
        handlers.GET_SECRET: [
        MessageHandler(
            Filters.all, handlers.accept_secret_code
        )],

        handlers.CUSTOMER_HOME: [
        MessageHandler(
            Filters.all, handlers.customer_home
        )],
        handlers.REGISTRATION_PAGE:[
            MessageHandler(
                Filters.all,handlers.handle_registration
            )
        ],
        handlers.AUTHENTICATE_ADMIN:[
            MessageHandler(
                Filters.all, handlers.authenticate_admin
            )
        ],
       handlers.ADMIN_ACTIONS:[
            MessageHandler(
            Filters.all,
            handlers.admin_actions
            )
       ],
       handlers.MANAGE_CATEGORY:[
        CallbackQueryHandler(handlers.manage_category),
        MessageHandler(
        Filters.all,
        handlers.admin_actions
        )
       ],
       handlers.ADD_CATEGORY:[
            MessageHandler(
                Filters.all,handlers.add_category,

            ),
            MessageHandler(
            Filters.all,
            handlers.admin_actions
            )
       ],
       handlers.ADD_AGAIN:[
        CallbackQueryHandler(handlers.add_again),
        MessageHandler(
        Filters.all,
        handlers.admin_actions
        )
       ],
       handlers.MANAGE_PRODUCT:[
         CallbackQueryHandler(handlers.manage_product),
         MessageHandler(
         Filters.all,
         handlers.admin_actions
         )
       ],
       handlers.ADD_PRODUCT:[
         MessageHandler(Filters.all,handlers.add_product),
         MessageHandler(
         Filters.all,
         handlers.admin_actions
         )
       ],
       handlers.DELETE_PRODUCT:[
         MessageHandler(Filters.all,handlers.delete_product),
         MessageHandler(
         Filters.all,
         handlers.admin_actions
         )
       ],
        handlers.EDIT_PRODUCT:[
          CallbackQueryHandler(handlers.edit_product),
          MessageHandler(
          Filters.all,
          handlers.admin_actions
          )
        ],
        #--------------------customers action------------------------#
        handlers.CUSTOMER_HOME:[
             MessageHandler(Filters.all,handlers.customer_home),
        ],
        handlers.SHOW_PRODUCTS_FROM_CAT:[
            MessageHandler(Filters.all,handlers.customer_home),
            CallbackQueryHandler(handlers.show_products_from_category)
        ],
        handlers.ADD_TO_CART:[
            MessageHandler(Filters.all,handlers.customer_home),
            CallbackQueryHandler(handlers.add_to_cart)
        ],
        handlers.REGISTER_ORDER:[
            MessageHandler(Filters.all,handlers.register_order),
            MessageHandler(Filters.all,handlers.customer_home),
        ],
        handlers.GENERATE_QRCODE:[
            CallbackQueryHandler(handlers.generate_qr_code),
            MessageHandler(Filters.all,handlers.customer_home),
        ],


    },
    fallbacks=[CommandHandler('cancel',handlers.cancel)],
    allow_reentry=True
)
dispatcher = updater.dispatcher
dispatcher.add_handler(com_handlers)
updater.start_polling()
# updater.start_webhook(listen="0.0.0.0",port=int(PORT), url_path=TOKEN,webhook_url = 'https://bitbazaarbot.herokuapp.com/' + TOKEN )
updater.idle()
