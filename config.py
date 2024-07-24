# devggn
# Note if you are trying to deploy on vps then directly fill values in ("")

from os import getenv

API_ID = int(getenv("API_ID", "28122413"))
API_HASH = getenv("API_HASH", "750432c8e1b221f91fd2c93a92710093")
BOT_TOKEN = getenv("BOT_TOKEN", "7186198304:AAEfo-rmJDbe-8w37JSP7e_r25mz5AhEdC4")
OWNER_ID = int(getenv("OWNER_ID", "7453770651"))
MONGODB_CONNECTION_STRING = getenv("MONGO_DB", "mongodb+srv://vikas:vikas@vikas.yfezexk.mongodb.net/?retryWrites=true&w=majority")
LOG_GROUP = int(getenv("LOG_GROUP", "-1001975521991"))
FORCESUB = getenv("FORCESUB", "-1001975521991")
