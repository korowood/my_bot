import re
import requests
import sys


def generate_name(realname):
    """
    Generate the new Wu Tang Clan name from a real name

    realname: String of your real name

    Example:

        >>> generate_name('Igor')
        'Misunderstood Overlord'

    Returns a string of generated Wu Tang Clan name
    """
    wutangclan_url = 'http://www.mess.be/inickgenwuname.php'

    response = requests.post(wutangclan_url, data={'realname': realname})
    response_text = response.content.decode('latin-1')  # decode('utf-8')

    start = response_text.find('<font size=2>') + 13
    end = response_text[start:].find('</b>')

    return response_text[start:][:end].replace('\n', '')

# name = generate_name('Igor')
#
# print(name)
