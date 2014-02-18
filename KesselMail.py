#/usr/bin/env python2

import smtplib
import imaplib
import email
import os, sys
import warnings
import hashlib
import logging
import daemon
from datetime import datetime
from time import sleep


from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


class KesselMail:
    def __init__(self,user = None, passw = None):
        self.username = user if user is not None else os.getenv("KesselMailUser")
        self.password = passw if user is not None else os.getenv("KesselMailPass")
        sentFile = os.getenv("KesselMailSentFile")
        logFile = os.getenv("KesselMailLogFile")
        self.sentFile =  sentFile if sentFile else "/var/KesselMail/KesselMailSentFile"
        self.logFile =  logFile if logFile else "/var/KesselMail/KesselMailLogFile"
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logFileHandler = logging.FileHandler(self.logFile,"a")
        self.logFileHandler.setLevel(logging.DEBUG)
        self.logger.addHandler(self.logFileHandler)
        
        imap = imaplib.IMAP4_SSL("imap.gmail.com","993")
        imap.login(self.username,self.password)
        imap.select()
        self.imap = imap
        with open(self.sentFile,"r") as f:
            self.alreadySent = map(lambda s: s.strip(),f.readlines())
        self.logger.info("Created")

    def __del__(self):
        self.imap.close()
        self.imap.logout()

    def start(self):
        self.logger.info("Starting KesselMail at " + str(datetime.now()))
        self.loop()

    def loop(self):
        while True:
            self.logger.info("Checking mail at " + str(datetime.now()))
            self.getMailAndConvertToTex()
            sleep(300) 
            
    def getFileToSend(self,mail):
        if mail.get_content_type() == "plain/text":
           link = mail.get_payload()
           filen = link.split("/")[-1]
           tempnam = os.tempnam()
           os.system("curl %s %s" % (link, tempnam))
           return (filen,tempnam)
           
    def createSend2KindleMessage(self,files):
        msg = MIMEMultipart()
        msgstring = "Enclosed are the files you sent to be downloaded"
        part1 = MIMEText(msgstring,"plain")
        msg.attach(part1)
        for (name,filename) in files:
            with open(filename,"rb") as fp:
                app = MIMEApplication(fp.read())
                app.replace_header("Content-Type","application/x-mobipocket-ebook;\r\n\tname=%s" %(name,))
                app.add_header("Content-Disposistion","attachment;\r\n\tname=%s" %(name,))
                msg.attach(app)

            os.remove(filename)
        msg["Subject"] = "%s" % (",".join(map(lambda (n,f):n,files)),)
        return msg

    def convMailPdfToTex(self,mail):
        if mail.get_content_type() == "application/pdf":
            filen = mail.get_filename()
            numdots = filen.count(".")
            newname = filen.replace(".","-",numdots-1).replace(" ","_").replace(")","").replace("(","")
            tempnam = os.tempnam()+".pdf"
            tempnam2 = os.tempnam()+".pdf"
            with open(tempnam,"wb") as fp:
                fp.write(mail.get_payload(decode=True))
            os.system("inkscape '%s' -z -D --export-latex -A '%s'" %( tempnam, tempnam2));
            os.remove(tempnam)
            return (newname,tempnam2)
            
        else:
            print "Incorrect file format"
                
    def logAsSent(self,msg):
        msg = msg.as_string()
        hashcode = hashlib.sha224(msg).hexdigest()
        with open(self.sentFile,"a") as f:
            f.write(hashcode+"\n")
        self.alreadySent.append(hashcode)

    def hasBeenSent(self,msg):
        msg = msg.as_string()
        hashcode = hashlib.sha224(msg).hexdigest()
        return hashcode in self.alreadySent


    def convEpubToMobi(self,m):
        return None
        
    def createConv2MobiMessage(self,files):
        pass

            
    def getMailAndConvertToTex(self, searchQuery = '(NOT SEEN)'):
        im = imaplib.IMAP4_SSL("imap.gmail.com","993")
        im.login(self.username,self.password)
        im.select()
        _,data = im.search(None,searchQuery)
        numFound = len(data[0].split())
        for num in data[0].split():
            _,data = im.fetch(num,'(RFC822)')
            msg = email.message_from_string(data[0][1])
            if not self.hasBeenSent(msg):
                payload = msg.get_payload()
                generatedFiles = []
                handled = False
                if ".pdf" in msg["Subject"] or msg["Subject"] == "Convert to TeX":
                    handled = True
                    for m in payload:
                        r = self.convMailPdfToTex(m)
                        if r:
                            handled = True
                            generatedFiles.append(r)
                    msgToSend = self.createConv2TexMessage(generatedFiles)
                #if ".epub" in msg["Subject"] or msg["Subject"] == "Convert to mobi":
                #    for m in payload:
                #        r = self.convEpubToMobi(m)
                #        if r:
                #            handled = True
                #            generatedFiles.append(r)
                #    msgToSend = self.createConv2MobiMessage(generatedFiles)
                if msg["Subject"] == "Send to Kindle":
                    for m in payload:
                        r = self.getFileToSend(m)
                        if r:
                            handled = True
                            generatedFiles.append(r)
                    msgToSend = self.createSend2KindleMessage(generatedFiles)
                if handled:
                    self.logger.info(msg["From"].split()[-1] + ", " + msgToSend["Subject"])
                    self.sendMail(msgToSend,msg["From"])
                    self.logAsSent(msg)
                
        im.close()
        im.logout()
        return numFound
            

    def createConv2TexMessage(self, files):
        msg = MIMEMultipart()
        msgstring = "Enclosed are the files you sent, converted to TeX."
        part1 = MIMEText(msgstring,"plain")
        msg.attach(part1)
        for (name,filename) in files:
            with open(filename,"rb") as fp:
                app = MIMEApplication(fp.read())
                app.replace_header("Content-Type","application/pdf;\r\n\tname=%s" %(name,))
                app.add_header("Content-Disposistion","attachment;\r\n\tname=%s" %(name,))
                print app.values()
                print app.keys()
                msg.attach(app)
            with open(filename+"_tex","rb") as fp:
                f = fp.read()
                f = f.replace(filename.split('/')[-1], name)
                app = MIMEApplication(f)
                app.replace_header("Content-Type","application/x-tex;\r\n\tname=%s" %(name+"_tex",))
                app.add_header("Content-Disposistion","attachment;\r\n\tname=%s" %(name+"_tex",))
                msg.attach(app)

            os.remove(filename)
            os.remove(filename+"_tex")
        msg["Subject"] = "%s converted to TeX." % (",".join(map(lambda (n,f):n,files)),)
        return msg
        
        
    def sendMail(self,msg,to):
        smtp = smtplib.SMTP("smtp.gmail.com:587")
        smtp.starttls()
        smtp.login(self.username,self.password)
        print "Sending mail to %s " %(to,)
        smtp.sendmail(self.username,to,msg.as_string())
        smtp.quit()

km = None
def init():
    global km
    km = KesselMail()

def getLogF():
    return km.logFileHandler
    

def main():
    km.start()

if __name__ == "__main__":
    init()
    main()
