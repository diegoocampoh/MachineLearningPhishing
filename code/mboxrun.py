# coding=utf-8
import mailbox
import utils
import pandas as pd
import re
import csv
from config import *
from BeautifulSoup import BeautifulSoup

# Internal features

# HTML content  DONE
# HTML form    DONE
# iFrames      DONE
# Attachments  DONE
# Potential XSS calls
# Flash content  DONE
# External resources in HTML header (css, js) DONE
# Javascript usage to hide URL link
# Using “@” in URLS
# Using hexadecimal characters in URLS
# Nonmatching URLS
# URL lengths
# Hostname lengths
# HREFs to IPs DONE


# Python 2
from abc import ABCMeta, abstractmethod


class FeatureFinder:
    __metaclass__ = ABCMeta

    @abstractmethod
    def getFeatureTitle(self):
        pass

    @abstractmethod
    def getFeature(self, message):
        pass


class HTMLFormFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Html Form"

    def getFeature(self, message):
        import re
        super(HTMLFormFinder, self).getFeature(message)
        payload = utils.getpayload(message).lower()
        return re.compile(r'<\s?\/?\s?form\s?>', re.IGNORECASE).search(payload) != None


class IFrameFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Html iFrame"

    def getFeature(self, message):
        import re
        super(IFrameFinder, self).getFeature(message)
        payload = utils.getpayload(message).lower()
        return re.compile(r'<\s?\/?\s?iframe\s?>', re.IGNORECASE).search(payload) != None


class FlashFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Flash content"

    def getFeature(self, message):
        import re
        super(FlashFinder, self).getFeature(message)
        payload = utils.getpayload(message).lower()

        swflinks = re.compile(FLASH_LINKED_CONTENT, re.IGNORECASE).findall(payload)
        flashObject = re.compile(r'embed\s*src\s*=\s*\".*\.swf\"', re.IGNORECASE).search(payload);
        return (swflinks != None and len(swflinks) > 0) or \
               (flashObject != None)


class AttachmentFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Attachments"

    def getFeature(self, message):
        return utils.getAttachmentCount(message)


class HTMLContentFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "HTML content"

    def getFeature(self, message):
        return utils.ishtml(message)


class URLsFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "URLs"

    def getFeature(self, message):
        return len(utils.geturls_payload(message))


class ExternalResourcesFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "External Resources"

    def getFeature(self, message):
        return len(utils.getexternalresources(message))


class JavascriptFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Javascript"

    def getFeature(self, message):
        return len(utils.getjavascriptusage(message))


class CssFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Css"

    def getFeature(self, message):
        return len(utils.getcssusage(message))


class IPsInURLs(FeatureFinder):
    def getFeatureTitle(self):
        return "IPs in URLs"

    def getFeature(self, message):
        return len(utils.getIPHrefs(message)) > 0


class AtInURLs(FeatureFinder):
    def getFeatureTitle(self):
        return "@ in URLs"

    def getFeature(self, message):
        emailPattern = re.compile(EMAILREGEX, re.IGNORECASE)
        for url in utils.geturls_payload(message):
            if (url.lower().startswith("mailto:") or (
                    emailPattern.search(url) != None and emailPattern.search(url).group() != None)):
                continue
            atvalue = url.find("@")
            athexvalue = url.find("%40")

            if (atvalue != -1 and athexvalue != -1):
                atvalue = min(athexvalue, atvalue)
            else:
                atvalue = max(atvalue, athexvalue)

            paramindex = url.find("?")

            if paramindex != -1:  # url has parameters, an email can be a parameter
                if (atvalue != -1) and (paramindex > atvalue):
                    return True
            else:
                # There are no parameters in the url. if there is an @, then return true
                if (atvalue != -1):
                    return True
        return False


class EncodingFinder(FeatureFinder):
    def getFeatureTitle(self):
        return "Encoding"

    def getFeature(self, message):
        return str(message.get('content-transfer-encoding')).lower()


def processFile(filepath, phishy=True, limit=500):
    mbox = mailbox.mbox(filepath)
    i = 1
    data = []

    email_index = []

    finders = [HTMLFormFinder(), AttachmentFinder(), FlashFinder(),
               IFrameFinder(), HTMLContentFinder(), URLsFinder(),
               ExternalResourcesFinder(), JavascriptFinder(),
               CssFinder(), IPsInURLs(), AtInURLs(), EncodingFinder()]
    for message in mbox:
        dict = {}

        totalsize = 0
        payload = utils.getpayload_dict(message)
        for part in payload:
                totalsize += len(re.sub(r'\s+','',part["payload"]))

        if totalsize < 1:
            print "empty email - "+str(phishy)+" - "+utils.getpayload(message)
            continue

        for finder in finders:
            dict[finder.getFeatureTitle()] = finder.getFeature(message)
        dict["Phishy"] = phishy
        data.append(dict)

        email_fields = {}
        email_fields["id"] = i
        email_fields["message"] = utils.getpayload(message)
        email_fields["raw"] = str(message)
        email_index.append(email_fields)
        i += 1
        if limit and i >= limit:
            break

    df = pd.DataFrame(data)
    df.to_csv(filepath + "-export", quoting=csv.QUOTE_ALL)

    emails = pd.DataFrame(email_index)
    emails.to_csv(filepath + "-export-index.csv")


def mboxtests():
    processFile("resources/phishing3.mbox", limit=2279)
    processFile("resources/enron-2279-mbox.mbox", limit=2257, phishy=False)


mboxtests()
