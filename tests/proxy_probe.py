import requests

# proxy_string = 'http://YBJ4Eq:u5HmBf@217.29.62.158:14866'
# proxyDict = {"http": proxy_string , "https": proxy_string}


proxies = {'http': 'http://YBJ4Eq:u5HmBf@217.29.62.158:14866',
           'https':  'http://YBJ4Eq:u5HmBf@217.29.62.158:14866'}
phone_agent = 'Mozilla/5.0'

url = 'https://2ip.ru/'
headers = {
        # "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
        "user-agent": phone_agent
    }
header = {''
          ''}
proxyDict = {
              "http"  : 'YBJ4Eq:u5HmBf@217.29.62.158:14866',
              # "https" : 'http://YBJ4Eq:u5HmBf@217.29.62.158:14866',
              # "ftp"   : ftp_proxy
            }


r = requests.get(url, proxies=proxyDict,headers=headers)
# print(r.text)



import urllib.request
import socket
import urllib.error


def is_bad_proxy(pip):
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': pip})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        urllib.request.install_opener(opener)
        req = urllib.request.Request('http://www.example.com')  # change the URL to test here
        sock = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        print('Error code: ', e.code)
        return e.code
    except Exception as detail:
        print("ERROR:", detail)
        return True
    return False


def main():
    socket.setdefaulttimeout(120)

    # two sample proxy IPs
    proxyList = ['125.76.226.9:80', '25.176.126.9:80']

    # for currentProxy in proxyList:



if __name__ == '__main__':
    # pass
    if is_bad_proxy('YBJ4Eq:u5HmBf@217.29.62.158:14866'):
        print("Bad Proxy %s" % ('YBJ4Eq:u5HmBf@217.29.62.158:14866'))
    else:
        print("%s is working" % ('YBJ4Eq:u5HmBf@217.29.62.158:14866'))
    # main()
    # proxy_handler = urllib.request.ProxyHandler({'http': 'YBJ4Eq:u5HmBf@217.29.62.158:14866'})
    # opener = urllib.request.build_opener(proxy_handler)
    # opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    # urllib.request.install_opener(opener)
    # req = urllib.request.Request(url)  # change the URL to test here
    # sock = urllib.request.urlopen(req)
    # print(sock.read().decode('utf8'))
    # print(req)
    # print(req.text)