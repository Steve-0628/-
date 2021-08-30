import requests
import json
import os
from pathlib import Path
import hashlib
import json_merge
from get_proxy import proxy

def calchash(filepath, thehash):
    try:
        with open(filepath,'rb') as f:
            readdata = f.read()
    except FileNotFoundError:
        return False
    return (hashlib.sha1(readdata).hexdigest() == thehash)


def getproxy():
    return proxy()

def download(releasetype="", id="", useproxy=False):
    THE_PROXY = ""
    if useproxy:
        THE_PROXY = getproxy()
        print("Using Proxy: ", THE_PROXY)
    print("making default paths...")
    Path("minecraft").mkdir(exist_ok=True)
    Path(os.path.join("minecraft", "versions")).mkdir(exist_ok=True)
    print("done")


    print("fetching manifest data...")
    manifesturl = THE_PROXY + "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    manifest = requests.get(manifesturl)
    manifestjson = json.loads(manifest.text)
    with open(os.path.join("minecraft", "versions", os.path.basename(manifesturl)) ,mode='w') as f: #
        f.write(manifest.text)
    print("done")


    # print(manifestjson["latest"])
    if releasetype != "all" and (not bool(releasetype)):
        releasetype = input("Select type, release, snapshot, old_alpha? ")
    versions = []
    verstr = ""


    print("selecting type...")
    if releasetype == "all":
        versions = manifestjson["versions"]
    else:
        for ver in manifestjson["versions"]:
            if ver["type"] == releasetype:
                versions.append(ver)
                verstr = verstr + ver["id"] + ", "
                # print(ver["id"])
    print("done")

    if not bool(id):
        id = input("Found versions, which do you want? " + verstr + " :")
    version = {}


    print("collecting version...")
    for ver in versions:
        if ver["id"] == id:
            version = ver
            break
    if bool(version) == False:
        if os.path.exists(os.path.join("minecraft", "versions", id)):
            with open(os.path.join("minecraft", "versions", id, id + ".json") ,mode='r') as f:
                versionjson = f.read()
                if "inheritsFrom" in versionjson:
                    versionjson = json_merge.merger(versionjson, json.load(open(os.path.join("minecraft", "versions", versionjson["inheritsFrom"], versionjson["inheritsFrom"]+".json"))))
        else:
            print("No version found. ")
            return
    print("done")

    if bool(version):
        print("fetching version data...")
        Path(os.path.join("minecraft", "versions", id)).mkdir(exist_ok=True)
        versiondata = requests.get(THE_PROXY + version["url"])
        versionjson = json.loads(versiondata.text)
        with open(os.path.join("minecraft", "versions", id, os.path.basename(version["url"])) ,mode='w') as f: 
            f.write(versiondata.text)
        print("done")


    print("collecting client jar...")
    path = os.path.join("minecraft", "versions", id, id + ".jar")
    if not calchash(path, versionjson["downloads"]["client"]["sha1"]):
        client = requests.get(THE_PROXY + versionjson["downloads"]["client"]["url"]).content


        with open(path ,mode='wb') as f: #
            f.write(client)
    else:
        print("Skipped download: hash matched.")
    print("done")


    print("collecting libraries...")
    libs = versionjson["libraries"]
    size = len(libs)
    print("downloading " + str(size) + " libraries...")
    libcount = 0
    for lib in libs:
        disallow = False
        libcount+=1
        print("(" + str(libcount) + "/" + str(size) + ")downloading " + lib["name"])
        tmp = ""
        if "rules" in lib:
            for rule in lib["rules"]:
                if "os" in rule:
                    if rule["os"]["name"] == "osx":
                        if rule["action"] == "disallow":
                            print("DISALLOW")
                            disallow = True
                    if rule["action"] == "allow" and rule["os"]["name"] != "osx":
                        disallow = True
        if not disallow:
            isnative = False
            try:
                if "natives" in lib:
                    if "osx" in lib["natives"]:
                        if "classifiers" in lib["downloads"]:
                            print("USING CLASSIFIERS")
                            tmp = lib["downloads"]["classifiers"][lib["natives"]["osx"]]
                            isnative = True
                            # print(tmp)
                        else: 
                            raise Exception
                    else: 
                        raise Exception
                else: 
                    raise Exception
            except Exception:
                try:
                    tmp = lib["downloads"]["artifact"]
                except KeyError:
                    print("KEY ERROR!!!!")
                    print(lib)
                    raise KeyError

            if "path" not in tmp:
                print("ERROR: path not in tmp!!!!!")
                print(tmp)
                print(lib)
            tmppath = tmp["path"]
            tmpdir = os.path.dirname(tmppath)
            Path(os.path.join("minecraft", "libraries", tmpdir)).mkdir(exist_ok=True, parents=True)

            if not calchash(os.path.join("minecraft", "libraries", tmp["path"]), tmp["sha1"]):

                lib = requests.get(THE_PROXY + tmp["url"])
                with open(os.path.join("minecraft", "libraries", tmp["path"]) ,mode='wb') as f: #
                    f.write(lib.content)
                if not calchash(os.path.join("minecraft", "libraries", tmp["path"]), tmp["sha1"]):
                    print("Hash does not match. Exiting...")
                    return -1
                if(isnative):
                    # It is an native file; unzip
                    pass
            else:
                print("Skipped: hash matches")
    print("done. ")


    print("fetching assets data...")
    assetsurl = versionjson["assetIndex"]["url"]
    assetsjson = {}
    if not calchash(os.path.join("minecraft", "assets", "indexes", os.path.basename(assetsurl)), versionjson["assetIndex"]["sha1"]):
        assetsr = requests.get(THE_PROXY + assetsurl)
        assetsjson = json.loads(assetsr.text)
        Path(os.path.join("minecraft", "assets", "indexes")).mkdir(exist_ok=True, parents=True)
        with open(os.path.join("minecraft", "assets", "indexes", os.path.basename(assetsurl)) ,mode='w') as f: 
            f.write(assetsr.text)
    else:
        with open(os.path.join("minecraft", "assets", "indexes", os.path.basename(assetsurl)),'r') as f:
            assetsjson = json.loads(f.read())
        print("Skipped version manifest: hash matches")

    objs = assetsjson["objects"]
    print("downloading " + str(len(assetsjson["objects"]))  + " assets...")
    Path(os.path.join("minecraft", "assets", "objects")).mkdir(exist_ok=True, parents=True)
    assetscount = 0
    for asset in objs:
        assetscount+=1
        print("(" + str(assetscount) + "/" + str(len(objs)) + ")" + "dowonloading " + asset + "...")
        if not calchash(os.path.join("minecraft", "assets", "objects", objs[asset]["hash"][:2], objs[asset]["hash"]), objs[asset]["hash"]):
            dling = requests.get(THE_PROXY + "http://resources.download.minecraft.net/" + objs[asset]["hash"][:2] + "/" + objs[asset]["hash"])
            Path(os.path.join("minecraft", "assets", "objects", objs[asset]["hash"][:2])).mkdir(exist_ok=True, parents=True)
            with open(os.path.join("minecraft", "assets", "objects", objs[asset]["hash"][:2], objs[asset]["hash"]) ,mode='wb') as f: 
                f.write(dling.content)
        else:
            print("Skipping asset: hash match")

    print("Done. ")

def getjava(type="jre-legacy", useproxy=False):
    THE_PROXY = ""
    if useproxy:
        THE_PROXY = getproxy()
    java_manifest_url = THE_PROXY + "https://launchermeta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"
    java_json = json.loads(requests.get(java_manifest_url).text)
    try:
        java_version_json = java_json["mac-os"][type]
    except KeyError:
        print("Java version not found. Stopping")
        return
    print(java_version_json)
    java_version_url = THE_PROXY + java_version_json[0]["manifest"]["url"]
    java_version = json.loads(requests.get(java_version_url).text)
    Path(os.path.join("minecraft", "runtime", type)).mkdir(exist_ok=True, parents=True)
    filecount = 1
    total = str(len(java_version["files"]))
    print("Starting to download", total, "files for java...")
    for item in java_version["files"]:
        i = java_version["files"][item]
        print("Downloading", "(" + str(filecount) + "/" + total + ")", item + "...")
        if i["type"] == "directory" or i["type"] == "link":
            print("Is directory/Is link")
            continue
        if not calchash(os.path.join("minecraft", "runtime", type, item), i["downloads"]["raw"]["sha1"]):
            file = requests.get(THE_PROXY + i["downloads"]["raw"]["url"])
            Path(os.path.join("minecraft", "runtime", type, os.path.dirname(item))).mkdir(parents=True, exist_ok=True)
            with open(os.path.join("minecraft", "runtime", type, item), "wb") as f:
                f.write(file.content)
            if not calchash(os.path.join("minecraft", "runtime", type, item), i["downloads"]["raw"]["sha1"]):
                print("Hash does not match. Exiting...")
                return -1
            if i["executable"]:
                print("File is executable...")
                os.chmod(os.path.join("minecraft", "runtime", type, item), 0o0777)
        else:
            print("Skipping file: Hash Match")
        filecount+=1



if __name__ == "__main__":
    getjava()