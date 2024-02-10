"""Utilities to assist with capturing user responses"""

import os
import os.path


def get_user_response_bool(
    message,
    prompt,
    error_msg="Error: Invalid response received - please enter a valid yes/no response!",
):
    """Prompt the user for a response, and return whether the response is true or false

    :param message: A message to display on the screen before the user input
    :type message: str
    :param prompt: The prompt to display next to the user input
    :type prompt: str
    :param error_msg: The error message to display if the user didn't respond with a truthie/falsie response, defaults to "Error: Invalid response received - please enter a valid yes/no response!"
    :type error_msg: str
    :return: Return true/false depending on what the user responded with
    :rtype: bool
    """
    while True:
        print(message)
        response = input(prompt).lower().strip()

        # assess the user response for a truthy/falsie response
        if response in ["true", "t", "y", "yes", "1"]:
            return True
        # user responded with a falsie statement
        elif response in ["false", "f", "n", "no", "0"]:
            return False
        # invalid response - start the loop again
        else:
            print(error_msg)
            continue  # restart the loop again


def get_user_response_path(
    message, prompt, error_msg="Error: Unable to find the path provided!"
):
    """Prompt the user for a response, and determine whether the response is a valid path or not

    :param message: A message to display on the screen before the user input
    :type message: str
    :param prompt: The prompt to display next to the user input
    :type prompt: str
    :param error_msg: The error message to display if the user didn't respond with a truthie/falsie response, defaults to "Error: Unable to find the path provided!"
    :type error_msg: str
    :return: Return the path the user entered if it is validated to exist
    :rtype: str
    """
    while True:
        print(message)
        response = input(prompt).strip()

        # define a Path object from the current file's directory
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), response)

        # check whether the path actually exists - if not, loop until we receive a valid input
        if not os.path.exists(path):
            print(error_msg)
            continue

        return path
