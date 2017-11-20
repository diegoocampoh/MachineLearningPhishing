from config import *
import re
from BeautifulSoup import BeautifulSoup
import urllib, sys
import pythonwhois
import pprint
import tldextract

def getpayload(msg):
    return __getpayload_rec__(msg, payloadresult="")


def __getpayload_rec__(msg, payloadresult):
    payload = msg.get_payload()

    if str(msg.get('content-transfer-encoding')).lower() == "base64":
        payload = msg.get_payload(decode=True)

    if payload and msg.is_multipart():
        for subMsg in payload:
            payloadresult += __getpayload_rec__(subMsg, payloadresult)
    else:
        return msg.get_content_type() + "\t" + payload + "\n"
    return payloadresult


def getpayload_dict(msg):
    return __getpayload_dict_rec__(msg, [])


def __getpayload_dict_rec__(msg, payloadresult):
    payload = msg.get_payload()
    if msg.is_multipart():
        for subMsg in payload:
            __getpayload_dict_rec__(subMsg, payloadresult)
    else:
        payloadresult.append({"mimeType": msg.get_content_type(), "payload": payload})
    return payloadresult


def getAttachmentCount(msg):
    return __getAttachmentCountrec__(msg, count=0)


def __getAttachmentCountrec__(msg, count):
    payload = msg.get_payload()
    if msg.is_multipart():
        for subMsg in payload:
            count += __getAttachmentCountrec__(subMsg, count)
    else:
        if __hasAttachment__(msg):
            return 1
    return count


def __hasAttachment__(message):
    contentDisp = message.get("Content-Disposition")
    return contentDisp is not None and contentDisp.lower().find("attachment") != -1


def getContentTypes(msg):
    return __getContentTypes_rec__(msg, [])


def __getContentTypes_rec__(msg, contenttypes):
    payload = msg.get_payload()
    if msg.is_multipart():
        for subMsg in payload:
            __getContentTypes_rec__(subMsg, contenttypes)
    else:
        contenttypes.append(msg.get_content_type())

    return contenttypes


def geturls_payload(message):
    """
    Returns the urls present in the message payload.
    Could be optimized by only looking into text payloads instead of all the payload

    :param message: message
    :return: url list
    """
    return geturls_string(getpayload(message))


def getIPHrefs(message):
    urls = geturls_payload(message)
    iphref = re.compile(IPREGEX, re.IGNORECASE)
    result = []
    for url in urls:
        if iphref.search(url) and iphref.search(url).group(1) is not None:
            result.append(iphref.search(url).group(1))
    return result


def getexternalresources(message):
    """
    :param message: message
    :return: url list-
    """
    result = []

    for script in getjavascriptusage(message):
        if "src" in str(script) and "src" in script and isurl(script["src"]):
            result.append(script["src"])
    for css in getcssusage(message):
        if "href" in str(css) and isurl(css["href"]):
            result.append(css["href"])

    return result


def getjavascriptusage(message):
    """
    :param message: message
    :return: url list-
    """
    result = []
    payload = getpayload_dict(message)
    for part in payload:
        if part["mimeType"].lower() == "text/html":
            htmlcontent = part["payload"]
            soup = BeautifulSoup(htmlcontent)
            scripts = soup.findAll("script")
            for script in scripts:
                result.append(script)
    return result


def getcssusage(message):
    """
    :param message: message
    :return: url list-
    """
    result = []
    payload = getpayload_dict(message)
    for part in payload:
        if part["mimeType"].lower() == "text/html":
            htmlcontent = part["payload"]
            soup = BeautifulSoup(htmlcontent)
            csslinks = soup.findAll("link")
            for css in csslinks:
                result.append(css)
    return result


def geturls_string(string):
    """
    Returns the urls present in the message payload.
    Could be optimized by only looking into text payloads instead of all the payload

    :param message: message
    :return: url list
    """
    result = []

    cleanPayload = re.sub(r'\s+', ' ', string)  # removes innecesary spaces
    linkregex = re.compile(HREFREGEX, re.IGNORECASE)
    links = linkregex.findall(cleanPayload)

    for link in links:
        if isurl(link):
            result.append(link)


    urlregex = re.compile(URLREGEX_NOT_ALONE, re.IGNORECASE)
    links = urlregex.findall(cleanPayload)
    for link in links:
        if link not in result:
            result.append(link)
    return links


def isurl(link):
    return re.compile(URLREGEX, re.IGNORECASE).search(link) is not None


def returnallmatches(string, regex):
    matches = re.finditer(regex, string, re.MULTILINE)
    result = []
    for match in enumerate(matches):
        result.append(match.group())
    return result


def get_alexa_rank(url):
    xml = urllib.urlopen('http://data.alexa.com/data?cli=10&dat=s&url=%s' % url).read()
    try:
        rank = int(re.search(r'RANK="(\d+)"', xml).groups()[0])
    except:
        rank = -1
    return rank


def extract_registered_domain(url):
    return tldextract.extract(url).registered_domain

def get_whois_data(url):
    domain = extract_registered_domain;
    return pythonwhois.get_whois(domain)


def ishtml(message):
    result = ("text/html" in getContentTypes(message))
    payload = getpayload_dict(message)
    for part in payload:
        if result or BeautifulSoup(part["payload"]).find():
            return True
    return result

