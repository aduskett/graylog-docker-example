#!/usr/bin/env python3
"""graylog_test.py
 The MIT License (MIT)
 Copyright (c) 2019 Adam Duskett
 
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 
 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.
 
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
 OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
 OR OTHER DEALINGS IN THE SOFTWARE.
"""
import argparse
import logging
import json
from urllib.parse import quote
import graypy
import requests
import elasticsearch


class CustomHelpFormatter(argparse.HelpFormatter):
    """Remove the space after the ',' when a blank metavar is used."""

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def graylog_server_api_call(graylog_server_ip, username, password, api_url):
    """Call a graylog server with a get request.

    :param graylog_server_ip: The ip of the Graylog server.
    :param username: The username of which to use.
    :param password: The password of which to use.
    :param api_url: The URL of the API call.
    :return: the response back from the server.
    """
    graylog_server_call = graylog_server_ip + '/api/' + api_url
    try:
        return requests.get(graylog_server_call, timeout=2,
                            auth=(username, password),
                            headers={"accept": "application/json"})

    except requests.exceptions.ConnectionError:
        logging.error("Timeout connecting to the graylog server at: %s", graylog_server_call)
        exit(1)


def remove_message(elastic_search_ip, username, password, message_id):
    """Remove a message from an elasticsearch server.

    :param elastic_search_ip: The IP of the elasticsearch server.
    :param username: The username of which to use.
    :param password: The password of which to use.
    :param message_id: The ID of the message of which to delete.
    """
    body = {"query": {"match": {"_id": message_id}}}
    elastic_search = elasticsearch.Elasticsearch(
        elastic_search_ip,
        http_auth=(username, password)
    )
    info = elastic_search.info()
    if not info:
        print("Could not connect to elasticsearch!")
        exit(1)
    check = elastic_search.search('_all', body=body)
    total = check['hits']['total']
    if total:
        check = elastic_search.delete_by_query('_all', body)
        if check['deleted'] == 1:
            print("Successfully deleted test message!")


def message_check(graylog_server_ip, graylog_server_port, username, password, message):
    """Check to see if the sent message was saved to the Graylog server.

    :param graylog_server_ip: The ip of the Graylog server.
    :param graylog_server_port: The port on which the Graylog server is running.
    :param username: The username of which to use.
    :param password: The password of which to use.
    :param message: The message that was sent.
    """
    graylog_server_url = "http://" + graylog_server_ip
    if graylog_server_port:
        graylog_server_url += ':' + graylog_server_port
    params = quote(message)
    keyword = quote("1 hour ago")
    query_url = 'search/universal/keyword?query=' + params + \
                '&keyword=' + keyword + \
                '&decorate=true'
    api_call_args = {
        'graylog_server_ip': graylog_server_url,
        'username': username,
        'password': password,
        'api_url': query_url
    }
    response = graylog_server_api_call(**api_call_args)

    try:
        response = response.json()
        data = json.loads(response['messages'][0]['message']['message'])
        if data['message'] != message:
            print("Message was not found or not logged!")
            exit(1)
        print("Successfully queried and found " + message + " from " + graylog_server_ip + "!")
        print("The Graylog server at " + graylog_server_ip + " seems to be working correctly!")
        remove_message(
            graylog_server_ip, username, password, response['messages'][0]['message']['_id']
        )
    except json.decoder.JSONDecodeError:
        print("ERROR! Got a response code of: " + str(response.status_code))
        print(response.text)
        exit(1)
    except IndexError:
        print("Error! Message does not exist!")
        exit(1)


def parse_args():
    """Parse arguments.

    :return: The argument object.
    """

    def help_format(prog):
        return CustomHelpFormatter(prog)

    parser = argparse.ArgumentParser(formatter_class=help_format)
    parser.add_argument("-c", "--connection-type",
                        type=str,
                        metavar='',
                        default="tcp",
                        help="Set a connection type.")

    parser.add_argument("-m", "--message",
                        type=str,
                        metavar='',
                        default="This is a test message.",
                        help="Send a message")

    parser.add_argument("-P", "--host-port",
                        type=str,
                        metavar='',
                        default='',
                        help="Specify the Graylog server host port.")

    parser.add_argument("-i", "--server-ip",
                        type=str,
                        metavar='',
                        default="127.0.0.1:9000",
                        help="Specify the Graylog server host ip.")

    parser.add_argument("-u", "--username",
                        type=str,
                        metavar='',
                        default="admin",
                        help="Specify the Graylog server username.")

    parser.add_argument("-p", "--password",
                        type=str,
                        metavar='',
                        default="password123456789!",
                        help="Specify the Graylog server password.")

    return parser.parse_args()


def main():
    """Send a message to a given Graylog server and then check to see if the log was saved."""
    args = parse_args()
    graylog_server = "http://" + args.server_ip
    if args.host_port:
        graylog_server += ':' + args.host_port

    graylog_server_api = graylog_server + '/api/'
    connection_type = args.connection_type.lower().strip()

    if connection_type not in ("udp", "tcp"):
        print("Connection type of " + connection_type + " is invalid. Valid options: UDP/TCP")
        exit(1)
    try:
        response_check = requests.get(graylog_server_api, auth=(args.username, args.password),
                                      headers={"accept": "application/json"},
                                      timeout=2)
        if response_check.status_code != 200:
            logging.error("Received response code: %s", str(response_check.status_code))
            exit(1)
        response_json = response_check.json()
        if not response_json['version']:
            logging.error("Failed to connect to the graylog server at: %s", graylog_server_api)
            exit(1)
        print("Connected to Graylog server at " + graylog_server + " with version "
              + response_json['version'])
    except requests.exceptions.ConnectionError:
        logging.error("Timeout connecting to the graylog server at: %s", graylog_server_api)
        exit(1)

    my_logger = logging.getLogger('graylog_logger')
    my_logger.setLevel(logging.DEBUG)
    if connection_type == "udp":
        graylog = graypy.GELFUDPHandler(args.server_ip)
    else:
        graylog = graypy.GELFTCPHandler(args.server_ip)

    my_logger.addHandler(graylog)
    print("Sending: " + args.message + " to the Graylog server!")

    jsondata = {"message": args.message}
    my_logger.debug(jsondata)
    # message_check(args.server_ip, args.host_port, args.username, args.password, args.message)


if __name__ == '__main__':
    main()
