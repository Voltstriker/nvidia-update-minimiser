""" Remove unnecessary bloat and telemetry from the Nvidia driver experience """

import sys
import os
import os.path
import subprocess
from shutil import rmtree
import xml.etree.ElementTree as xml
import re
import tempfile
import uuid
import winreg
import user_utils


def unzip_file(zip_location, destination_folder, password=""):
    """Unzip a zip file using 7zip

    :param zip_location: The location of the zip file to unzip
    :type zip_location: str
    :param destination_folder: The location to unzip the zip's contents
    :type destination_folder: str
    :param password: The password of the zip (if applicable), defaults to ""
    :type password: str, optional
    :return: Return a dict denoting the success of the operation
    :rtype: dict
    """

    # Ensure the zip file exists
    if not os.path.exists(zip_location):
        return {"success": False, "msg": "Unable to locate the zip file"}

    # Ensure the destination folder exists
    if not os.path.isdir(destination_folder):
        return {"success": False, "msg": "Unable to locate the destination folder"}

    # Build the array of arguments to pass to the shell
    cmd = [
        get_7zip_installation(),  # location of the 7-zip program
        "x",  # unzip
        zip_location,  # the zip to target
        f"-o{destination_folder}",  # destination folder
        "-r",  # recurse subdirectories (maintain folder structure)
        "-y",  # respond yes to any prompts
    ]

    # If the zip is password protected, add the password as an additional parameter
    if password:
        cmd.append(f"-p{password}")

    # Unzip silently by outputting 7zip to os.devnull
    with open(os.devnull) as null:  # pylint: disable=unspecified-encoding
        # Execute the command, outputting any messages to a null terminal
        process = subprocess.run(
            cmd,
            stderr=null,
            stdout=null,
            shell=True,
            check=True,  # check the result of the operation after completion
        )

    return {
        "success": process.returncode == 0,  # Success = 0, anything wrong <> 0
        "msg": "Unzip completed successfully",
    }


def get_7zip_installation():
    """Returns the path of the 7z.exe file from the 7-Zip installation folder

    :return: The path to the 7z.exe file
    :rtype: str
    """

    # Query the 7-Zip registry key
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"Software\7-Zip")
    path = winreg.QueryValueEx(key, "Path")[0]

    # Return the path
    path_7z = os.path.join(path, "7z.exe")
    return path_7z


def edit_cfg_file(working_folder):
    """Adjust the Nvidia update config file to remove certain references that we removed

    :param working_folder: The working folder used to unzip the driver file contents
    :type working_folder: str
    """
    # edit the cfg file to remove certain items that aren't needed
    cfg_file_path = os.path.join(working_folder, "setup.cfg")
    rgx = re.compile(
        r"\${{EulaHtmlFile}}|\${{FunctionalConsentFile}}|\${{PrivacyPolicyFile}}"
    )

    # parse the cfg file, and obtain the root element
    cfg_file = xml.parse(cfg_file_path)
    # find the <manifest> node tree
    manifest_tree = cfg_file.findall("manifest")
    for manifest in manifest_tree:
        # find the <file> node tree within <manifest>
        file_tree = manifest.findall("file")
        for file in file_tree:
            # if the <file> node has an attr matching the files deleted earlier
            result = rgx.findall(file.get("name"))
            if len(result) > 0:
                # delete the <file> node
                clean_name = result[0].translate({ord(i): None for i in r"$\{\}"})
                print(f" > Removing reference to '{clean_name}'")
                manifest.remove(file)

    # write the adjustments back to the cfg file
    cfg_file.write(cfg_file_path)


def remove_driver_bloat(working_folder):
    """Remove folders and files from the driver contents once it has been unzipped

    :param working_folder: The working folder used to unzip the driver file contents
    :type working_folder: str
    """
    # list of files/folders to keep
    items_to_keep = {
        "folders": ["Display.Driver", "NVI2", "PhysX"],
        "files": ["EULA.txt", "ListDevices.txt", "setup.cfg", "setup.exe"],
    }

    try:
        # remove all unnecessary folders
        driver_contents = os.listdir(working_folder)
        for item in driver_contents:
            item_path = os.path.join(working_folder, item)
            # check if a valid folder
            if os.path.isdir(item_path):
                # check if folder is in the list of folders to keep
                if item not in items_to_keep["folders"]:
                    # delete the folder and it's contents
                    print(f" > Deleting folder '{item}'")
                    rmtree(item_path)
            # is not a folder - is a file
            else:
                if item not in items_to_keep["files"]:
                    print(f" > Deleting file '{item}'")
                    rmtree(item_path)

    except FileNotFoundError as ex:
        print(f"Something went wrong deleting the driver bloat: {ex}")
    except OSError as ex:
        print(f"Something went wrong deleting the driver bloat: {ex}")


def launch_update(working_folder):
    """Launch the Nvidia driver installation

    :param working_folder: The working folder used to unzip the driver file contents
    :type working_folder: str
    :return: Return a dict denoting the success of the operation
    :rtype: dict
    """
    exe_location = os.path.join(working_folder, "setup.exe")

    # Build the array of arguments to pass to the shell
    cmd = [exe_location, "-nosplash", "-noeula", "-passive", "-noreboot", "-nofinish"]

    with open(os.devnull) as null:  # pylint: disable=unspecified-encoding
        # Execute the command, outputting any messages to a null terminal
        process = subprocess.run(
            cmd,
            stderr=null,
            stdout=null,
            shell=True,
            check=True,  # check the result of the operation after completion
        )

    return {
        "success": process.returncode == 0,  # Success = 0, anything wrong <> 0
        "msg": "Update completed successfully",
    }


def nvidia_update_minimiser():
    """Remove unnecessary bloat and telemetry from the Nvidia driver experience"""

    print("=========================================")
    print("     Nvidia Driver Update Minimiser      ")
    print("=========================================")

    # request the location of the Nvidia driver downloaded from the website from the user
    driver_location = user_utils.get_user_response_path(
        "\nEnter the location of the Nvidia driver that has been downloaded..",
        "File Path: ",
        "Error: Unable to find the driver at the path specified!",
    )

    # define a working directory within the user's temp files folder
    uid = str(uuid.uuid4())
    working_directory = os.path.join(
        tempfile.gettempdir(), "NvidiaUpdateMinimiser", uid
    )

    try:
        print("\nCreating working folder to use during installation process..")
        # make a temporary to use for the application
        os.makedirs(working_directory, exist_ok=True)

        print("\nUnzipping driver..")
        unzip_status = unzip_file(driver_location, working_directory)

        # check whether the unzip was unsuccessful
        if not unzip_status["success"]:
            print("Something went wrong..")
            sys.exit(0)

        # remove folder/file bloat from the unzip directory
        print("\nRemoving driver bloat..")
        remove_driver_bloat(working_directory)

        # adjust the driver cfg file to remove references to certain files/folders
        print("\nAdjusting driver configuration file..")
        edit_cfg_file(working_directory)

        # check whether to launch the driver exe
        run_exe = user_utils.get_user_response_bool(
            "\nDo you want to launch the driver installation?", "Start Upgrade (Y/N): "
        )
        # if we want to launch the exe:
        if run_exe:
            print("\nLaunching the Nvidia driver installation..")
            print(" > Installation running")
            update_status = launch_update(working_directory)

            if not update_status["success"]:
                print("Error: something went wrong while executing the driver upgrade!")
                sys.exit(0)

            print(" > Installation completed")

            # Clean up the working directory after installation
            print("\nCleaning up the working directory used..")
            rmtree(working_directory)

    except Exception as ex:  # pylint: disable=broad-exception-caught
        print(f"Something went wrong: {ex}")


if __name__ == "__main__":
    nvidia_update_minimiser()
    print("\nApplication finished..")
