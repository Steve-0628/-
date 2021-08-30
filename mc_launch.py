import mc_data, mc_login, json_merge
import sys
import os
import json
import zipfile
from pathlib import Path
import subprocess
from shutil import rmtree

def launch(version="", userdata={}, useproxy=False):

    java_args = {}
    java_special_args = []

    if "user" not in userdata:
        print("Please log in first...")
        username = input("Your email/username:")
        pswd = input("Your password:")
        if useproxy:
            userdata=mc_login.seigen_login(username, pswd)
        else:
            userdata = mc_login.login(username, pswd)
    if not bool(version):
        version=input("What version?")

    version_path=os.path.join("minecraft", "versions", version)
    jar_path = os.path.join(version_path, version+".jar")
    natives_path = os.path.join("minecraft", "natives")

    java_args["-Djava.library.path"] = os.path.abspath(natives_path)
    java_args["-Dminecraft.client.jar"] = os.path.abspath(jar_path)
    java_args["-Dminecraft.launcher.brand"] = "python_launcher"
    java_args["-Dminecraft.launcher.version"] = "v0.0.3"


    version_manifest = json.load(open(os.path.join("minecraft", "versions", "version_manifest.json")))
    # version_exists = False
    # for ver in version_manifest["versions"]:
    #     if ver["id"] == version:
    #         version_exists = True
    #         break
    # if not version_exists:
    #     print("The version does not exist; try another")
    #     return
    if not os.path.exists(version_path):
        if(input("Version does not exist. Do you want do download(y/No)") == "y"):
            mc_data.download("all", version, useproxy=useproxy)
    version_json = json.load(open(os.path.join(version_path, version+".json")))

    # For Forge...
    print(version_json["mainClass"])
    if "inheritsFrom" in version_json:
        version_json = json_merge.merger(json.load(open(os.path.join("minecraft", "versions", version_json["inheritsFrom"], version_json["inheritsFrom"]+".json"))), version_json)
    print(version_json["mainClass"])

    java_cmd = ""

    print("Collecting java runtime..")
    if "javaVersion" in version_json:
        jvmtype = version_json["javaVersion"]["component"]
        mc_data.getjava(jvmtype, useproxy=useproxy)
        java_cmd = os.path.abspath(os.path.join("minecraft", "runtime", jvmtype, "jre.bundle", "Contents", "Home", "bin", "java")).replace(" ", "\ ")
    else:
        mc_data.getjava(useproxy=useproxy)
        java_cmd = os.path.abspath(os.path.join("minecraft", "runtime", "jre-legacy", "jre.bundle", "Contents", "Home", "bin", "java")).replace(" ", "\ ")

    version_libs = version_json["libraries"]
    print("Extracting native libraries...")
    Path(natives_path).mkdir(exist_ok=True)

    java_cp_arg = []

    for lib in version_libs:
        disallow = False
        if "rules" in lib:
            for rule in lib["rules"]:
                if "os" in rule:
                    if rule["os"]["name"] == "osx":
                        if rule["action"] == "disallow":
                            disallow = True
                    if rule["action"] == "allow" and rule["os"]["name"] != "osx":
                        disallow = True
        if not disallow:
            try:
                if "natives" in lib:
                    if "osx" in lib["natives"]:
                        if "classifiers" in lib["downloads"]:
                            # print("USING CLASSIFIERS")
                            tmp = lib["downloads"]["classifiers"][lib["natives"]["osx"]]
                            nativelibpath = os.path.join("minecraft", "libraries", tmp["path"])
                            with zipfile.ZipFile(nativelibpath, "r") as zip:
                                zip.extractall((os.path.join("minecraft", "natives")))
                            continue
                        else:
                            raise Exception
                    else:
                        raise Exception
                else:
                    raise Exception
            except Exception:
                tmp = lib["downloads"]["artifact"]
                libpath = os.path.abspath(os.path.join("minecraft", "libraries", tmp["path"])).replace(" ", "\ ")
                java_cp_arg.append(libpath)
    java_cp_arg.append(os.path.abspath(jar_path).replace(" ", "\ "))

    java_special_args.append("-cp")
    java_special_args.append(":".join(java_cp_arg))

    # java_special_args.append("-XstartOnFirstThread")

    java_special_args.append("-Xmx2G")
    java_special_args.append("-Xms512M")

    print("Generating minecraft arguments...")
    minecraft_args = {}
    i = 0
    # for arg in version_json["minecraftArguments"].split():
    #     if i % 2 == 0:
    #         minecraft_args[arg] = ""
    #     i+=1

    minecraft_args["--version"] = version
    minecraft_args["--gameDir"] = os.path.abspath(os.path.join("minecraft"))
    minecraft_args["--assetsDir"] = os.path.abspath(os.path.join("minecraft", "assets"))
    minecraft_args["--assetIndex"] = version_json["assetIndex"]["id"]
    minecraft_args["--userType"] = "mojang"
    minecraft_args["--versionType"] = "release"
    minecraft_args["--username"] = userdata["selectedProfile"]["name"]
    minecraft_args["--uuid"] = userdata["selectedProfile"]["id"]
    minecraft_args["--accessToken"] = userdata["accessToken"]
    minecraft_args["--userProperties"] = "{}"

    minecraft_arg = version_json["minecraftArguments"]
    minecraft_arg = minecraft_arg \
                        .replace("${auth_player_name}", userdata["selectedProfile"]["name"]) \
                        .replace("${version_name}", version) \
                        .replace("${game_directory}", os.path.abspath(os.path.join("minecraft"))) \
                        .replace("${assets_root}", os.path.abspath(os.path.join("minecraft", "assets"))) \
                        .replace("${assets_index_name}", version_json["assetIndex"]["id"]) \
                        .replace("${auth_uuid}", userdata["selectedProfile"]["id"]) \
                        .replace("${auth_access_token}", userdata["accessToken"]) \
                        .replace("${user_type}", "mojang") \
                        .replace("${version_type}", "release") \
                        .replace("${auth_session}", userdata["accessToken"])
                        

    print("Combining java and minecraft args...")
    # java_cmd = "java"
    minecraft = java_cmd + " "
    for item in java_args:
        minecraft += item + "=" +  java_args[item].replace(" ", "\ ") + " " + " "
    for item in java_special_args:
        minecraft += item + " "
    minecraft += version_json["mainClass"]  + " "  # + userdata["selectedProfile"]["name"] + " " + userdata["accessToken"] + " "

    # for item in minecraft_args:
    #     minecraft += item + " " +  minecraft_args[item].replace(" ", "\ ") + " "
    minecraft += minecraft_arg
    print()
    print(minecraft)
    os.system(minecraft)
    # Path(natives_path).rmdir()
    rmtree(natives_path)


def launcher():
    # username = input("Your email/username:")
    # pswd = input("Your password:")
    # login_json = mc_login.login(username, pswd)
    login_json = {}
    print("## PyLauncher v0.0.3 ##")
    print("Type \"help\" for help")
    print("You'd better login first!")
    sel = ""
    useproxy = False
    sels = ["exit", "launch", "help", "download", "login", "superlogin", "proxy"]
    while(sel != "exit"):
        sel = input("Enter command:")
        if sel == "offline":
            print("Offline Mode... Work in Progress")
            userdata = {} 
            userdata["selectedProfile"] = {}
            userdata["selectedProfile"]["name"] = "user123"
            userdata["selectedProfile"]["id"] = "THE_SUPER_UUID_YOU_WANT"
            userdata["accessToken"] = "WHAT_EVER_ACCESS_TOKEN_YOU_MIGHT_WANT"
            userdata["user"] = {}
            login_json = userdata
            continue
        if sel not in sels:                                 # Command not found error
            print("Command \"", sel, "\" is not recognized. ")
            print("Use one of:", sels)
        if sel == "help":                                   # Help
            print("Use one of:", sels)
        if sel=="proxy":
            useproxy = not useproxy
            print("Set useproxy to: ", useproxy)
        if sel == "download":                               # Download
            print("Starting download...")
            mc_data.download(useproxy=useproxy)
        if sel == "login":                                  # login
            print("Logging in...")
            username = input("Your email/username:")
            pswd = input("Your password:")
            login_json = mc_login.login(username, pswd)
            print("Login data:")
            print(login_json)
        if sel == "superlogin":                                  # login
            print("Super Logging in...")
            username = input("Your email/username:")
            pswd = input("Your password:")
            login_json = mc_login.seigen_login(username, pswd)
            print("Login data:")
            print(login_json)
        if sel == "launch":                                 # Launch
            print("Launching some versions may not work.")
            try:
                launch(userdata=login_json, useproxy=useproxy)
            except Exception as e:
                print("Error occurd while launching/running Minecraft. ")
                print(e.with_traceback(e.__traceback__))


    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    launcher()