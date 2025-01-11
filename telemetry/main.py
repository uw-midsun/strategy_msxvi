from decoder import DatagramDecoder
from db_upload import Upload

decoder = DatagramDecoder()
db = Upload()

while True:
    decoder.read()
    db.upload()
